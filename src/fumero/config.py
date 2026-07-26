"""What gets documented, and where the result goes.

A [`Config`] is the single argument every other part of fumero takes, so adding an option does not
mean widening a chain of function signatures. It is immutable: derive a variant with
[`Config.replace`] rather than mutating one that something else already holds.
"""

import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, fields, replace
from enum import StrEnum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Self, cast

import griffe

__all__ = ["Config", "Dialect"]


class Dialect(StrEnum):
    """A docstring dialect griffe knows how to parse.

    [`Dialect.AUTO`] leaves the choice to griffe, which reads the shape of each docstring and picks
    for itself. Name one of the others when a package mixes styles and the guess lands wrong.
    """

    AUTO = "auto"
    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"


@dataclass(frozen=True)
class Config:
    """What to document, how much of it, and where the result goes.

    Every field has a default, so `Config()` on its own is valid and documents everything into the
    working directory. Use [`Config.from_pyproject`] to take the defaults from a project file.

    Attributes:
        output: Directory the `.mdx` tree is written into.
        base_url: URL the output directory is served at, used to build links between pages. Leave
            it empty for links relative to the site root.
        dialect: The docstring dialect griffe parses with.
        exclude: Glob patterns matched against each member's dotted path and its short name.
            Excluding a module drops its whole subtree.
        clean: Remove the module's previous output before rendering.
        with_source: Render each function's own source below it, in a block that starts collapsed.
        with_meta: Write a `meta.json` in each output directory naming the pages it holds, which
            is how Fumadocs orders the sidebar. Submodules come before classes, each group under
            a heading of its own when a directory holds both. Without one the order is alphabetical.
    """

    output: Path = Path(".")
    base_url: str = ""
    dialect: Dialect = Dialect.AUTO
    exclude: tuple[str, ...] = ()
    clean: bool = False
    with_source: bool = False
    with_meta: bool = False

    @classmethod
    def from_pyproject(cls, path: Path | str = "pyproject.toml", **overrides: Any) -> Self:
        """Read the defaults from a `[tool.fumero]` table.

        A missing file, or a file with no such table, yields the defaults. Reading configuration is
        not an error when there is none to read. Keys naming no field are ignored, so a config file
        written for a later fumero does not break an earlier one.

        Every key is the field it sets, with hyphens allowed in place of underscores.

        Args:
            path: The `pyproject.toml` to read.
            **overrides: Values applied on top of the file, as [`Config.replace`] would.

        Returns:
            The configuration the file describes, with `overrides` applied.

        Examples:
            ```toml
            [tool.fumero]
            output = "content/docs/api"
            base-url = "/docs/api"
            exclude = ["example.internal", "*.tests"]
            with-meta = true
            ```
        """

        file = Path(path)
        table: dict[str, Any] = {}
        if file.is_file():
            loaded = tomllib.loads(file.read_text()).get("tool", {}).get("fumero", {})
            table = cast(dict[str, Any], loaded)

        names = {field.name for field in fields(cls)}
        values = {
            name: value for key, value in table.items() if (name := key.replace("-", "_")) in names
        }

        return cls(**_coerce(values)).replace(**overrides)

    def replace(self, **changes: Any) -> Self:
        """A copy with `changes` applied, skipping any whose value is `None`.

        Skipping `None` is what lets the command line hand over every flag it knows about and have
        the unset ones fall through to whatever the config file said.

        Args:
            **changes: Field values to override.

        Returns:
            A new configuration. The one this was called on is untouched.
        """

        given = {key: value for key, value in changes.items() if value is not None}

        return replace(self, **_coerce(given))

    def excludes(self, obj: griffe.Object | griffe.Alias) -> bool:
        """Whether `obj` matches one of the [`Config.exclude`] patterns.

        Patterns are matched against the dotted path and against the short name, so
        `example.internal` skips one module, `*.tests` skips every `tests` submodule, and a bare
        `deprecated` skips any member of that name wherever it turns up.

        Args:
            obj: The member to test.

        Returns:
            `True` when the member should be left undocumented.
        """

        return any(
            fnmatch(str(obj.path), pattern) or fnmatch(obj.name, pattern)
            for pattern in self.exclude
        )

    def href(self, segments: Sequence[str]) -> str:
        """The URL of the page at `segments`, under [`Config.base_url`].

        Args:
            segments: The page's path, one directory per element.

        Returns:
            An absolute URL path.

        Examples:
            ```python
            Config(base_url="/docs/api").href(["example", "core"])
            # '/docs/api/example/core'
            ```
        """

        return self.base_url.rstrip("/") + "/" + "/".join(segments)


def _coerce(values: dict[str, Any]) -> dict[str, Any]:
    """Turn loosely typed input, from a TOML table or a command line, into the field types."""

    coerced: dict[str, Any] = {}
    for name, value in values.items():
        match name:
            case "output":
                coerced[name] = Path(cast(str, value))

            case "exclude":
                coerced[name] = tuple(str(item) for item in cast(Sequence[object], value))

            case "dialect":
                coerced[name] = Dialect(value)

            case _:
                coerced[name] = value

    return coerced
