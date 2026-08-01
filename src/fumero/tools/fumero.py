"""The `fumero` command line.

A thin adapter. It turns arguments into a [`Config`], calls the same public API any other caller
would, and formats what comes back. Everything it can do is available from Python.

Options layer the way you would expect: a flag beats a `[tool.fumero]` key, which beats the
defaults. Every flag parses as `None` when it is not given, so an unset one falls through instead
of overwriting a configured value with an argparse default.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from ..component import init
from ..config import Config, Dialect
from ..error import FumeroException
from ..render import generate

__all__ = ["build_parser", "main"]

_OVERRIDES = (
    "output",
    "base_url",
    "dialect",
    "no_inspect",
    "exclude",
    "clean",
    "with_source",
    "with_meta",
)


def build_parser() -> argparse.ArgumentParser:
    """The argument parser, exposed so the documentation and shell completions can read it.

    Returns:
        A parser for the `init` and `generate` commands.
    """

    parser = argparse.ArgumentParser(prog="fumero", description="Generate .mdx from Python API")
    commands = parser.add_subparsers(title="commands", dest="command", required=True)

    initialiser = commands.add_parser("init", help="write the component file that renders the .mdx")
    _ = initialiser.add_argument(
        "path", type=Path, help="path for the component file (e.g. src/components/mdx/pdx.tsx)"
    )

    generator = commands.add_parser("generate", help="generate .mdx for a python module")
    _ = generator.add_argument("module", help="the module to generate documentation for")
    _ = generator.add_argument(
        "--output", "-o", type=Path, help="directory to write the documentation into"
    )
    _ = generator.add_argument(
        "--clean",
        action="store_true",
        default=None,
        help="remove the module's previously generated output before rendering",
    )

    parse_options = generator.add_argument_group("parse options")
    _ = parse_options.add_argument(
        "--dialect",
        type=Dialect,
        choices=Dialect,
        help="docstring dialect griffe parses (default: auto)",
    )
    _ = parse_options.add_argument(
        "--no-inspect",
        action="store_true",
        default=None,
        help="read a compiled module from the .pyi stubs beside it rather than by importing it",
    )
    _ = parse_options.add_argument(
        "--exclude",
        nargs="+",
        help="glob matched against a member's path or name (e.g. 'example.internal', '*.tests')",
    )

    output_options = generator.add_argument_group("output options")
    _ = output_options.add_argument(
        "--base-url",
        help="url the output directory is served at, used to build links (e.g. '/docs/api')",
    )
    _ = output_options.add_argument(
        "--with-source",
        action="store_true",
        default=None,
        help="render each function's own source below it, in a block that starts collapsed",
    )
    _ = output_options.add_argument(
        "--with-meta",
        action="store_true",
        default=None,
        help="write the meta.json files that order the fumadocs sidebar",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line.

    Args:
        argv: Arguments to parse, defaulting to `sys.argv`.

    Returns:
        A process exit status: `0` on success, `1` on a [`FumeroException`].
    """

    arguments = build_parser().parse_args(argv)

    try:
        if arguments.command == "init":
            print(f"wrote {init(cast(Path, arguments.path))}")

            return 0

        return _generate(arguments)

    except FumeroException as error:
        print(f"error: {error}", file=sys.stderr)

        return 1


def _generate(arguments: argparse.Namespace) -> int:
    """Document a module, and say what happened.

    Every flag is handed over whether it was given or not, because [`Config.replace`] drops the
    ones that came through as `None`. That is what layers the flags over the config file.
    """

    overrides = {name: getattr(arguments, name) for name in _OVERRIDES}
    config = Config.from_pyproject(**overrides)
    result = generate(cast(str, arguments.module), config)

    # an item link that names nothing is a typo or a stale rename, and rendering it as plain code
    # would hide that. the run still succeeds, because the pages are otherwise fine.
    for link in result.unresolved:
        print(f"warning: {link}", file=sys.stderr)

    print(f"wrote {len(result.pages)} pages to {config.output}")

    return 0
