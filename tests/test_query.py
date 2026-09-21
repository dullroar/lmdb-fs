from __future__ import annotations

from lmdb_fs.paths import parse_path


def test_matching_files_are_visible_at_each_query_level(query) -> None:  # type: ignore[no-untyped-def]
    root = query.listing()
    by_year = query.listing(parse_path("year=2026"))
    covid = query.listing(parse_path("year=2026/disease=COVID"))

    assert root.matched_nodes == frozenset({1, 2, 3, 4, 5})
    assert by_year.matched_nodes == frozenset({1, 2, 3, 5})
    assert covid.matched_nodes == frozenset({1, 2, 5})
    assert [entry.node_id for entry in covid.files] == [1, 2, 5]


def test_order_equivalence_and_used_facet_suppression(query) -> None:  # type: ignore[no-untyped-def]
    forward = query.listing(parse_path("year=2026/disease=COVID"))
    reverse = query.listing(parse_path("disease=COVID/year=2026"))
    assert forward.matched_nodes == reverse.matched_nodes
    assert {(entry.facet, entry.value) for entry in forward.facets} == {
        (entry.facet, entry.value) for entry in reverse.facets
    }
    assert {entry.facet for entry in forward.facets}.isdisjoint({"year", "disease"})


def test_nonempty_children_and_redundant_facets_are_visible(query) -> None:  # type: ignore[no-untyped-def]
    listing = query.listing(parse_path("year=2026/disease=flu"))
    assert ("species", "mouse") in {(entry.facet, entry.value) for entry in listing.facets}
    for entry in listing.facets:
        child = query.listing(query.child_predicates(listing.predicates, entry.facet, entry.value))
        assert child.matched_nodes


def test_virtual_filenames_are_unique_and_portable(query) -> None:  # type: ignore[no-untyped-def]
    files = query.listing().files
    assert len({file.name for file in files}) == len(files)
    assert all("/" not in file.name for file in files)
    assert any("%2F" in file.name and "%3D" in file.name for file in files)
