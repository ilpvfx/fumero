"""Writing a module out as Fumadocs MDX.

[`generate`] does the whole job in one call. [`Renderer`] is the same job with the pieces left
exposed, for when you already hold a loaded module or a collected [`LinkTable`] and want to reuse
it rather than build it again.

Nothing here prints. A run reports what it wrote and what it could not link through [`Result`],
and the caller decides whether any of that is worth showing anyone.
"""

import json
import shutil
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import griffe
import jinja2

from .config import Config
from .link import LinkTable
from .mdx import callout_type, encode_text, escape_identifier, fence, jsx_props, summarize
from .model import Card, Class, Module, ParsedDocstring
from .parse import load_module, module_attributes, parse_class, parse_function, public_members

__all__ = ["Renderer", "Result", "UnresolvedLink", "generate"]

_TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class UnresolvedLink:
    """An item link that named nothing documented.

    Attributes:
        path: The path exactly as the docstring wrote it.
        page: The file being rendered when the link was found.
    """

    path: str
    page: Path

    def __str__(self) -> str:
        return f"item link `{self.path}` in {self.page} matched no documented item"


@dataclass
class Result:
    """What a run produced.

    Attributes:
        pages: Every `.mdx` file written, in the order they were written.
        unresolved: The item links that named nothing documented. Each one is a typo or a stale
            rename, and each renders as plain code rather than as a link leading nowhere.
    """

    pages: list[Path] = field(default_factory=list)
    unresolved: list[UnresolvedLink] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Whether every link resolved."""

        return not self.unresolved


def generate(module: str, config: Config | None = None) -> Result:
    """Document a module.

    Args:
        module: An importable module path.
        config: What to render and where. Defaults document everything into the working directory.

    Returns:
        The files written, and any links that did not resolve.

    Raises:
        ModuleNotFound: `module` is not importable from here.

    Examples:
        ```python
        result = generate("example", Config(output=Path("content/docs/api"), clean=True))

        for link in result.unresolved:
            print(link)
        ```
    """

    config = config or Config()

    return Renderer(config).render(load_module(module, config), config.output)


class Renderer:
    """Walks a module tree and writes its MDX.

    Holds the configuration and the link table, so neither has to be threaded through the
    recursion. One renderer handles one tree; make another for another package.

    Args:
        config: What to render and where.
    """

    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self._links: LinkTable = LinkTable()
        self._result: Result = Result()
        self._scope: str | None = None
        self._page: Path = Path()
        self._environment: jinja2.Environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(_TEMPLATE_DIR)
        )

        template_globals: dict[str, Any] = {
            "jsx_props": jsx_props,
            "links_for": self._links_for,
            "link_for": self._link_for,
            "signature_links": self._signature_links,
        }
        template_filters: dict[str, Any] = {
            "encode": self._encode,
            "callout_type": callout_type,
            "fence": fence,
            "ident": escape_identifier,
            "summarize": summarize,
        }
        self._environment.globals.update(template_globals)
        self._environment.filters.update(template_filters)

    def _links_for(self, annotation: str | None) -> dict[str, str] | None:
        """Every documented type named in a signature, so the components can link them."""

        return self._links.types_in(annotation, self._scope)

    def _signature_links(self, docstring: ParsedDocstring) -> dict[str, str] | None:
        """Every documented type a definition names, gathered from the annotations behind it.

        Read from the annotations rather than from the rendered `def` line, because that line
        holds parameter names too. A parameter named after something documented would otherwise
        be linked as though it were the type.

        Args:
            docstring: The parsed docstring whose parameters and return type to read.

        Returns:
            The name to URL pairs, or `None` when the signature names nothing documented.
        """

        annotations = [parameter.annotation for parameter in docstring.parameters]
        if docstring.returns is not None:
            annotations.append(docstring.returns.annotation)

        found: dict[str, str] = {}
        for annotation in annotations:
            found.update(self._links.types_in(annotation, self._scope) or {})

        return found or None

    def _link_for(self, name: str) -> str | None:
        """One name rather than every name in a signature.

        An exception in a raises block is a single type, and the template needs its href to decide
        whether to link it at all.
        """

        return self._links.resolve(name, self._scope)

    def _encode(self, value: str | None) -> str:
        return encode_text(value, self._links, self._scope, self._record_unresolved)

    def render(self, module: griffe.Module, root: Path) -> Result:
        """Write `module` and everything under it into `root`.

        Link collection runs first, over the whole tree, so a page written early can point at a
        symbol whose own page is written later.

        Args:
            module: The module to write, as [`load_module`] returns it.
            root: The directory to write into.

        Returns:
            The files written, and any links that did not resolve.
        """

        self._result = Result()
        self._links = LinkTable.collect(module, self.config)

        if self.config.clean:
            self._clean(module.name, root)

        self._render_module(module, root)

        return self._result

    def _clean(self, name: str, root: Path) -> None:
        """Remove a module's previous output.

        A module owns `<root>/<name>.mdx` when it is a leaf and `<root>/<name>/` when it holds
        pages. Both go, so a renamed or deleted symbol leaves no orphan page behind.
        """

        (root / f"{name}.mdx").unlink(missing_ok=True)

        directory = root / name
        if directory.is_dir():
            shutil.rmtree(directory)

    def _record_unresolved(self, path: str) -> None:
        self._result.unresolved.append(UnresolvedLink(path, self._page))

    def _render_module(self, module: griffe.Module, root: Path) -> None:
        config = self.config
        name = module.name

        submodules = [
            cast(griffe.Module, member)
            for member in public_members(module, griffe.Kind.MODULE, config)
        ]
        classes = sorted(
            (
                parse_class(cast(griffe.Class, member), config)
                for member in public_members(module, griffe.Kind.CLASS, config)
            ),
            key=lambda parsed: parsed.name,
        )

        for parsed in classes:
            # a class holding nested classes becomes a directory with an index; otherwise a page
            if parsed.classes:
                directory = root / name / parsed.name
                self._render_class(parsed, directory / "index.mdx")
                for nested in parsed.classes:
                    self._render_class(nested, directory / f"{nested.name}.mdx")

                self._write_meta(directory, classes=sorted(n.name for n in parsed.classes))

            else:
                self._render_class(parsed, root / name / f"{parsed.name}.mdx")

        functions = sorted(
            (
                parse_function(cast(griffe.Function, member))
                for member in public_members(module, griffe.Kind.FUNCTION, config)
            ),
            key=lambda function: function.name,
        )

        page = Module(
            name=name,
            docstring=module.docstring.value if module.docstring else None,
            attributes=module_attributes(module, config),
            functions=functions,
            classes=classes,
            modules=[
                Card(child.name, child.docstring.value if child.docstring else None)
                for child in submodules
            ],
        )

        # a module owns a directory only when something goes inside it
        holds_pages = bool(classes) or bool(submodules)
        path = root / name / "index.mdx" if holds_pages else root / f"{name}.mdx"
        self._render_template("module.mdx.j2", {"module": page}, path)

        self._write_meta(
            root / name,
            modules=sorted(child.name for child in submodules),
            classes=sorted(parsed.name for parsed in classes),
        )

        for submodule in submodules:
            self._render_module(submodule, root / name)

    def _render_class(self, parsed: Class, path: Path) -> None:
        self._scope = parsed.name
        try:
            self._render_template("class.mdx.j2", {"class": parsed}, path)
        finally:
            self._scope = None

    def _render_template(self, template: str, context: dict[str, object], path: Path) -> None:
        self._page = path
        rendered = self._environment.get_template(template).render(
            with_source=self.config.with_source, **context
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(rendered)
        self._result.pages.append(path)

    def _write_meta(
        self, directory: Path, *, modules: Sequence[str] = (), classes: Sequence[str] = ()
    ) -> None:
        """Write the `meta.json` that fixes the order of the pages in one directory.

        Submodules come before classes, since a submodule opens a subtree and a class documents a
        single symbol. Their icons say which is which, so neither group needs a heading over it.
        """

        if not self.config.with_meta:
            return

        pages = [*modules, *classes]
        if not pages:
            return

        # fumadocs includes the index automatically, so it is never listed here
        _ = (directory / "meta.json").write_text(json.dumps({"pages": pages}, indent=2) + "\n")
