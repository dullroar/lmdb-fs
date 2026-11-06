---
gist: "Read when: changing the FUSE adapter, LMDBFSQuery, the MetadataBackend protocol or the LMDB index layout."
---

# Architecture

```text
ordinary POSIX programs
        |
     pyfuse3 adapter
        |
LMDBFSQuery (paths, predicates, directory construction)
        |
 MetadataBackend protocol
        |
   LMDB inverted index ---- immutable local payload paths
```

`LMDBFSQuery` is deliberately independent of both pyfuse3 and LMDB. It
receives a canonical predicate set and produces matching virtual files plus
remaining nonempty facet/value directories. The same query engine is exercised
against an in-memory inverted-index oracle and the LMDB backend.

## LMDB layout

- `nodes`: big-endian node ID to deterministic JSON node record.
- `facet_postings`: duplicate-sorted `(facet, value)` key to big-endian node
  IDs. This avoids a giant value for common facets and gives deterministic
  posting order.
- `facet_values`: duplicate-sorted facet name to values (reserved for future
  remaining-facet optimization).
- `metadata`: schema facet list and node count.

Intersections materialize the smallest duplicate-posting list first. The first
pass calculates remaining facet counts by scanning metadata of the matched set;
this is intentional and benchmarked separately from intersection time.

## Virtual paths and inodes

Facet directories are percent-encoded `facet=value` components. Encoding is
UTF-8, reversible, and escapes `/`, `=`, `%`, whitespace, and shell-sensitive
characters. A facet can only occur once; attempted repeated facets are not
emitted and lookup returns `ENOENT`.

Query results use a canonical sorted predicate key, while FUSE inode identity
also includes the visible parent. Thus alternate traversal orders produce the
same result set and preserve useful POSIX `..` navigation within a mount.
Files are named `<node_id>--<escaped-display-name>`, avoiding silent collisions.

## Read-only boundary

Payloads remain outside LMDB. `open` obtains an underlying read-only descriptor
and `read` uses `pread`; no payload is copied into the index. Create, write,
truncate, rename, unlink, rmdir, mkdir, symlink, and metadata mutations return
`EROFS` from the adapter.
