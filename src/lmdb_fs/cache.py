"""Tiny bounded LRU cache with auditable hit/miss counters."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    size: int
    capacity: int


class BoundedLRU(Generic[K, V]):
    """A zero-capacity cache is a useful explicit no-cache mode."""

    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("cache capacity cannot be negative")
        self.capacity = capacity
        self._items: OrderedDict[K, V] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: K) -> V | None:
        try:
            value = self._items.pop(key)
        except KeyError:
            self._misses += 1
            return None
        self._hits += 1
        self._items[key] = value
        return value

    def put(self, key: K, value: V) -> None:
        if self.capacity == 0:
            return
        self._items.pop(key, None)
        self._items[key] = value
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)
            self._evictions += 1

    def stats(self) -> CacheStats:
        return CacheStats(self._hits, self._misses, self._evictions, len(self._items), self.capacity)
