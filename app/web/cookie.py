"""Packing values for the session cookie: compact JSON, compressed, as URL-safe text.

Browsers silently drop cookies over 4 KB, so the household profile and the week's log are
packed before they go into the signed session.
"""

import base64
import json
import zlib


def pack(value: object) -> str:
    """Compact JSON, compressed, as URL-safe text for the cookie.

    Browsers silently drop cookies over 4 KB. Plain JSON of an eight-person household with
    Hindi names plus a week's log came to about 9 KB; packed, it is under 2 KB.

    Args:
        value: Any JSON-serialisable value.

    Returns:
        The packed text.

    >>> unpack(pack({"name": "दादी"}))
    {'name': 'दादी'}
    """
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(zlib.compress(data, 9)).decode()


def unpack(text: object) -> object:
    """The value packed by `pack`, or None when there is nothing readable.

    Args:
        text: What the cookie holds.

    Returns:
        The value, or None.
    """
    if not isinstance(text, str):
        return None
    try:
        return json.loads(zlib.decompress(base64.urlsafe_b64decode(text)))
    except (ValueError, zlib.error):
        return None
