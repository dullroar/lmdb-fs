from __future__ import annotations

import pytest

from semanticfs.paths import PathError, canonicalize, decode_component, encode_component, parse_path


@pytest.mark.parametrize(
    ("facet", "value"),
    [
        ("year", "2026"),
        ("disease", "COVID 19"),
        ("odd/facet", "a/b=c % 😀"),
        ("日本語", "München"),
    ],
)
def test_component_round_trip(facet: str, value: str) -> None:
    encoded = encode_component(facet, value)
    assert "/" not in encoded
    assert decode_component(encoded) == (facet, value)


def test_path_canonicalizes_order_without_rewriting_component_rules() -> None:
    assert parse_path("year=2026/disease=COVID") == parse_path("disease=COVID/year=2026")
    assert canonicalize((("year", "2026"), ("disease", "COVID"))) == (
        ("disease", "COVID"),
        ("year", "2026"),
    )


@pytest.mark.parametrize("path", ["year=2026/year=2025", "year=%", "year=", "year=2026=bad"])
def test_invalid_path_is_rejected(path: str) -> None:
    with pytest.raises(PathError):
        parse_path(path)
