#!/usr/bin/env python3
"""Compatibility entry point for build_indexes.py.

Run me when: an existing command calls the former index builder by name.
Usage: build_context_indexes.py [--check] [ROOT]
"""
import sys

from build_indexes import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
