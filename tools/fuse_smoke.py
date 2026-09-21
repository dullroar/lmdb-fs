#!/usr/bin/env python3
"""Minimal pyfuse3 mount used only to prove the host FUSE environment."""

from __future__ import annotations

import argparse
import errno
import os
import stat
from pathlib import Path

import pyfuse3
import trio


class HelloFS(pyfuse3.Operations):
    """A one-file, read-only filesystem for environment verification."""

    file_inode = pyfuse3.ROOT_INODE + 1
    file_name = b"message.txt"
    contents = b"semanticfs fuse smoke test\\n"

    async def getattr(self, inode, ctx=None):  # type: ignore[no-untyped-def]
        entry = pyfuse3.EntryAttributes()
        if inode == pyfuse3.ROOT_INODE:
            entry.st_mode = stat.S_IFDIR | 0o555
            entry.st_size = 0
        elif inode == self.file_inode:
            entry.st_mode = stat.S_IFREG | 0o444
            entry.st_size = len(self.contents)
        else:
            raise pyfuse3.FUSEError(errno.ENOENT)
        entry.st_atime_ns = entry.st_ctime_ns = entry.st_mtime_ns = 0
        entry.st_gid = os.getgid()
        entry.st_uid = os.getuid()
        entry.st_ino = inode
        return entry

    async def lookup(self, parent_inode, name, ctx):  # type: ignore[no-untyped-def]
        if parent_inode != pyfuse3.ROOT_INODE or name != self.file_name:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return await self.getattr(self.file_inode, ctx)

    async def opendir(self, inode, ctx):  # type: ignore[no-untyped-def]
        if inode != pyfuse3.ROOT_INODE:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return pyfuse3.FileHandleT(inode)

    async def readdir(self, fh, start_id, token):  # type: ignore[no-untyped-def]
        if fh != pyfuse3.ROOT_INODE:
            raise pyfuse3.FUSEError(errno.ENOENT)
        if start_id == 0:
            pyfuse3.readdir_reply(token, self.file_name, await self.getattr(self.file_inode), 1)

    async def open(self, inode, flags, ctx):  # type: ignore[no-untyped-def]
        if inode != self.file_inode:
            raise pyfuse3.FUSEError(errno.ENOENT)
        if flags & (os.O_WRONLY | os.O_RDWR):
            raise pyfuse3.FUSEError(errno.EROFS)
        return pyfuse3.FileInfo(fh=pyfuse3.FileHandleT(inode))

    async def read(self, fh, off, size):  # type: ignore[no-untyped-def]
        if fh != self.file_inode:
            raise pyfuse3.FUSEError(errno.ENOENT)
        return self.contents[off : off + size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mountpoint", type=Path)
    args = parser.parse_args()
    options = set(pyfuse3.default_options)
    options.add("fsname=semanticfs-smoke")
    pyfuse3.init(HelloFS(), os.fspath(args.mountpoint), options)
    try:
        trio.run(pyfuse3.main)
    finally:
        pyfuse3.close(unmount=False)


if __name__ == "__main__":
    main()
