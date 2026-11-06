---
gist: "Read when: changing how paths map to queries, facet and child-directory rules, path encoding, or the files shown at a query directory."
---

# A path is an accumulated metadata predicate

**Decision.** A directory path is a set of facet/value predicates, not physical containment: `/year=2026/disease=COVID/lab=LANL/` means `year = 2026 AND disease = COVID AND lab = LANL`.

**Invariants.**

- Every matching data object is visible as a file at every query directory.
- Child directories are unused facet/value predicates that occur among the current matches; no empty child is emitted.
- A facet appears at most once in a path, bounding depth by the configured facet count and preventing loops.
- Predicate order does not change the result set. Internally predicate pairs are canonicalized and share cache keys; the displayed path stays the caller's navigation history.
- Facet values are reversibly percent-encoded, so `/`, `=`, whitespace, Unicode and shell-significant characters never make a path ambiguous.
- Payloads remain external immutable files.

**Open experiment, not a rule.** The prototype shows a valid remaining facet even when it would not reduce the result set, which keeps the current result set legible. Whether a `hide_redundant_facets` option improves navigation is a later experiment.
