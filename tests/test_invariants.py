from __future__ import annotations

from itertools import permutations

from hypothesis import given, strategies as st

from semanticfs.paths import canonicalize


def test_all_permutations_have_identical_results(query) -> None:  # type: ignore[no-untyped-def]
    predicates = (("year", "2026"), ("disease", "COVID"), ("lab", "LANL"))
    expected = query.listing(canonicalize(predicates)).matched_nodes
    for order in permutations(predicates):
        assert query.listing(canonicalize(order)).matched_nodes == expected


@given(st.permutations((("year", "2026"), ("disease", "COVID"), ("lab", "LANL"))))
def test_property_order_canonicalization_is_stable(order) -> None:  # type: ignore[no-untyped-def]
    assert canonicalize(order) == canonicalize(reversed(order))


def test_monotonic_filtering_and_finite_depth(query, backend) -> None:  # type: ignore[no-untyped-def]
    root = query.listing()
    assert len(root.predicates) <= len(backend.facets)
    for entry in root.facets:
        child = query.listing(query.child_predicates(root.predicates, entry.facet, entry.value))
        assert child.matched_nodes <= root.matched_nodes
        assert len(child.predicates) <= len(backend.facets)
