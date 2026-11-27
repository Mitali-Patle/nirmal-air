"""A small in-process cache that can also hand back an expired value when a source is down.

Each server instance keeps its own copy, which is enough here: values are small, and a
miss costs one quick request. The oldest entries are dropped once `max_items` is reached, so
memory stays bounded however many places and households are looked up.
"""

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class Cached[T]:
    """A cached value and whether it is past its time to live."""

    value: T
    stale: bool


class TtlCache[T]:
    """Values kept for `ttl_s` seconds, and as a stale fallback for `keep_s` seconds."""

    def __init__(
        self,
        ttl_s: float,
        keep_s: float,
        max_items: int = 512,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._ttl_s = ttl_s
        self._keep_s = keep_s
        self._max_items = max_items
        self._clock = clock
        self._items: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> Cached[T] | None:
        """The value under `key`, marked stale once past its time to live.

        Args:
            key: Cache key.

        Returns:
            The cached value, or None when absent or too old even as a fallback.
        """
        item = self._items.get(key)
        if item is None:
            return None
        age = self._clock() - item[0]
        if age > self._keep_s:
            del self._items[key]
            return None
        return Cached(value=item[1], stale=age > self._ttl_s)

    def put(self, key: str, value: T) -> None:
        """Store a value, replacing any older one.

        Args:
            key: Cache key.
            value: Value to keep.
        """
        self._items.pop(key, None)
        if len(self._items) >= self._max_items:
            del self._items[next(iter(self._items))]
        self._items[key] = (self._clock(), value)


# After a source fails, it is not asked again for this long: callers use what they have.
QUIET_AFTER_FAILURE_S = 120.0


class RecentFailures:
    """Which sources failed in the last `quiet_s` seconds.

    A service that is down is then not waited on again by every request, each wait being a
    full timeout.
    """

    def __init__(
        self, quiet_s: float = QUIET_AFTER_FAILURE_S, clock: Callable[[], float] = monotonic
    ) -> None:
        self._failed: TtlCache[bool] = TtlCache(quiet_s, quiet_s, clock=clock)

    def note(self, key: str) -> None:
        """Remember that `key` just failed.

        Args:
            key: The source, such as a station name or "weather:<place>".
        """
        self._failed.put(key, True)

    def recent(self, key: str) -> bool:
        """Whether `key` failed within the quiet period.

        Args:
            key: The source.

        Returns:
            True while the source should not be asked again.
        """
        found = self._failed.get(key)
        return found is not None and not found.stale
