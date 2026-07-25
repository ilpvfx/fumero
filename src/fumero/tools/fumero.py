"""The `fumero` command line."""

import argparse
import sys
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """The argument parser, exposed so the documentation and shell completions can read it."""

    parser = argparse.ArgumentParser(prog="fumero", description="Generate .mdx from Python API")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line.

    Args:
        argv: Arguments to parse, defaulting to `sys.argv`.

    Returns:
        A process exit status: `0` on success, `1` on an [`Exception`].
    """

    _ = build_parser().parse_args(argv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
