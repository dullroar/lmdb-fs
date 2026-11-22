#!/usr/bin/env python3
"""Compatibility entry point for scan_secrets.py.

Run me when: an existing command calls the former secret scanner by name.
Usage: scan_context_secrets.py [ROOT]
"""
import sys

from scan_secrets import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
