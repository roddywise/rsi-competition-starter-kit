"""Participant entrypoint for the contest_harness SDK."""

import sys

from contest_harness.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
