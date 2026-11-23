"""Rebuild `app/air/stations.json`, the list of CPCB monitoring stations and where they are.

Readings are always fetched live; only the station names and positions are stored, because
they rarely change and a stored list makes finding the nearest station instant.

Usage: uv run python -m scripts.refresh_stations   (reads DATA_GOV_API_KEY from .env)
"""

import json
import time
from pathlib import Path

import httpx

from app.air.cpcb import CPCB_URL, USER_AGENT
from app.config import get_settings

OUTPUT = Path(__file__).resolve().parent.parent / "app" / "air" / "stations.json"
PAGE_SIZE = 1000
ATTEMPTS = 3


def fetch_page(client: httpx.Client, api_key: str, offset: int) -> dict[str, object]:
    """Fetch one page of rows, retrying because the API sometimes stalls for minutes.

    Args:
        client: HTTP client to use.
        api_key: data.gov.in API key.
        offset: Index of the first row to fetch.

    Returns:
        The decoded JSON page.

    Raises:
        httpx.HTTPError: If every attempt fails.
    """
    params: dict[str, str | int] = {
        "api-key": api_key,
        "format": "json",
        "limit": PAGE_SIZE,
        "offset": offset,
    }
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = client.get(CPCB_URL, params=params)
            response.raise_for_status()
            page: dict[str, object] = response.json()
        except httpx.HTTPError:
            if attempt == ATTEMPTS:
                raise
            time.sleep(20 * attempt)
        else:
            return page
    raise AssertionError("unreachable")  # pragma: no cover


def main() -> None:
    """Download every row, keep one entry per station and write the sorted list."""
    key = get_settings().data_gov_api_key
    if key is None:
        raise SystemExit("Set DATA_GOV_API_KEY in .env first.")
    stations: dict[str, dict[str, object]] = {}
    with httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
        offset, total = 0, 1
        while offset < total:
            page = fetch_page(client, key.get_secret_value(), offset)
            total = int(str(page["total"]))
            rows = page["records"]
            if not isinstance(rows, list):
                raise SystemExit(f"Unexpected reply at offset {offset}: {str(page)[:200]}")
            for row in rows:
                # Kept exactly as CPCB writes it (some names end in a space): the live query
                # matches the name character for character.
                stations[row["station"]] = {
                    "name": row["station"],
                    "city": row["city"].strip(),
                    "state": row["state"].strip().replace("_", " "),
                    "lat": round(float(row["latitude"]), 5),
                    "lon": round(float(row["longitude"]), 5),
                }
            offset += PAGE_SIZE
    ordered = sorted(stations.values(), key=lambda s: (s["state"], s["city"], s["name"]))
    lines = ",\n".join(json.dumps(station, ensure_ascii=False) for station in ordered)
    OUTPUT.write_text(f"[\n{lines}\n]\n", encoding="utf-8")
    print(f"Wrote {len(ordered)} stations to {OUTPUT.name}")


if __name__ == "__main__":
    main()
