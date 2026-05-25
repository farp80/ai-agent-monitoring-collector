#!/usr/bin/env python3
"""Entry point for the machine monitoring collector."""

from collector.app import CollectorApplication


def main() -> None:
    raise SystemExit(CollectorApplication().run())


if __name__ == "__main__":
    main()
