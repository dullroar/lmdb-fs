"""Reversible and unambiguous facet-path encoding."""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import quote_from_bytes

from .model import Predicate, PredicateKey

_SAFE = b"-._~"
_PERCENT_ESCAPE = re.compile(r"%(?:[0-9a-fA-F]{2})")


class PathError(ValueError):
    """A path cannot represent a valid SemanticFS query."""


def _encode(value: str) -> str:
    if "\x00" in value:
        raise PathError("NUL is not valid in a pathname component")
    return quote_from_bytes(value.encode("utf-8"), safe=_SAFE.decode("ascii"))


def _decode(value: str) -> str:
    position = 0
    while position < len(value):
        if value[position] == "%":
            match = _PERCENT_ESCAPE.match(value, position)
            if match is None:
                raise PathError(f"malformed percent escape in {value!r}")
            position = match.end()
        else:
            position += 1
    try:
        decoded = bytes(value, "ascii").decode("ascii") if value.isascii() else value
        # quote_from_bytes emits ASCII, but accepting literal Unicode keeps paths usable.
        raw = bytearray()
        index = 0
        while index < len(decoded):
            if decoded[index] == "%":
                raw.append(int(decoded[index + 1 : index + 3], 16))
                index += 3
            else:
                raw.extend(decoded[index].encode("utf-8"))
                index += 1
        result = bytes(raw).decode("utf-8", "strict")
    except UnicodeError as exc:
        raise PathError(f"invalid UTF-8 escape in {value!r}") from exc
    if not result or "\x00" in result:
        raise PathError("empty or NUL pathname token")
    return result


def encode_component(facet: str, value: str) -> str:
    """Encode ``facet=value`` as one portable virtual directory name."""

    return f"{_encode(facet)}={_encode(value)}"


def decode_component(component: str) -> Predicate:
    """Decode one directory component, rejecting ambiguous spellings."""

    if component in {"", ".", ".."} or component.count("=") != 1:
        raise PathError(f"invalid facet component {component!r}")
    raw_facet, raw_value = component.split("=", 1)
    return _decode(raw_facet), _decode(raw_value)


def canonicalize(predicates: Iterable[Predicate]) -> PredicateKey:
    """Sort predicates and reject a repeated facet before any backend call."""

    values = list(predicates)
    facets = [facet for facet, _ in values]
    if len(set(facets)) != len(facets):
        raise PathError("a facet may occur at most once in a query path")
    return tuple(sorted(values))


def parse_path(path: str | Iterable[str]) -> PredicateKey:
    """Parse slash-separated virtual components into the canonical query key."""

    parts = path.strip("/").split("/") if isinstance(path, str) else list(path)
    if parts == [""]:
        return ()
    return canonicalize(decode_component(part) for part in parts)


def render_path(predicates: Iterable[Predicate]) -> str:
    """Render a canonical path for logging/tests, not to rewrite user paths."""

    return "/" + "/".join(encode_component(facet, value) for facet, value in canonicalize(predicates))
