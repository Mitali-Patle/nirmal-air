"""Failures of the outside services the app reads from, one type per service."""


class UpstreamUnavailableError(Exception):
    """An outside service did not answer in time, or answered with nothing usable."""


class AirDataUnavailableError(UpstreamUnavailableError):
    """CPCB or the forecast did not answer in time, or answered without usable readings."""


class PlaceSearchError(UpstreamUnavailableError):
    """The place search (geocoder) failed."""


class WeatherUnavailableError(UpstreamUnavailableError):
    """The current weather could not be fetched (it only feeds the sky drawing)."""
