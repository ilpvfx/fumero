"""Where each documented name is rendered, so a docstring can point at one by name.

A [`LinkTable`] is built before anything is written, which is what lets a page link to a symbol
whose own page comes later. It records every spelling a docstring might plausibly use, from fully
qualified down to bare, against the URL that spelling should reach.

Only the names collected here resolve. That is deliberate: a reference that misses stays plain
text rather than turning into a link that scrolls nowhere.
"""

from collections.abc import Iterator, Mapping, Sequence
from typing import Self, cast

import griffe

from .config import Config
from .parse import module_attributes, public_members

__all__ = ["LinkTable", "expand_self"]

# members that live under an anchor on their owner's page, rather than getting a page of their own
_ANCHORED_KINDS = frozenset({griffe.Kind.ATTRIBUTE, griffe.Kind.FUNCTION})


class LinkTable(Mapping[str, str]):
    """Every documented name, mapped to where it is rendered.

    Behaves as a read-only mapping of path to URL, so one can be inspected, merged, or written out
    by hand. Use [`LinkTable.collect`] to build one from a module.

    Args:
        routes: An existing path to URL mapping to start from, such as one collected from another
            package that this one should link into.

    Examples:
        ```python
        table = LinkTable.collect(module, config)

        table.resolve("example.Client.close")    # '/api/example/Client#close'
        table.resolve("close", scope="Client")   # '/api/example/Client#close'
        ```
    """

    def __init__(self, routes: Mapping[str, str] | None = None) -> None:
        self._routes: dict[str, str] = dict(routes or {})

    def __getitem__(self, path: str) -> str:
        return self._routes[path]

    def __iter__(self) -> Iterator[str]:
        return iter(self._routes)

    def __len__(self) -> int:
        return len(self._routes)

    def __repr__(self) -> str:
        return f"LinkTable({len(self._routes)} paths)"

    @classmethod
    def collect(cls, module: griffe.Module, config: Config) -> Self:
        """Walk `module` and record where each documented name will be rendered.

        Mirrors the layout the renderer produces, so a collected URL always names a page that is
        actually written.

        Args:
            module: The module to walk, as [`load_module`] returns it.
            config: Decides what is rendered, and supplies the base URL.

        Returns:
            A table covering the whole tree.
        """

        return cls(_collect(module, [], config))

    def resolve(self, path: str, scope: str | None = None) -> str | None:
        """The URL for `path`, or `None` when nothing documented goes by that name.

        Resolution is scope first: a bare name is tried against `scope` before the package as a
        whole, so `close` written on the `Client` page means `Client.close` rather than some
        unrelated module function of the same name.

        Args:
            path: A name to look up. Fully qualified (`example.Client.close`), partly qualified
                (`Client.close`), bare (`close`), or written against the page being rendered
                (`self`, `self.close`).
            scope: The name of the page being rendered, when there is one.

        Returns:
            The URL, or `None` when the path names nothing documented.
        """

        if _is_self_path(path):
            return self._routes.get(expand_self(path, scope)) if scope else None

        if scope and (href := self._routes.get(f"{scope}.{path}")):
            return href

        return self._routes.get(path)

    def types_in(self, types: Sequence[str], scope: str | None = None) -> dict[str, str] | None:
        """The name to URL pairs for the documented types a signature names.

        This is what lets a rendered signature turn its types into links. It is given the names
        the parser resolved rather than a string to search, because a name alone cannot say what
        it refers to: `Path` is `pathlib.Path` in one module and a documented class in another.

        Args:
            types: Names the documented module defines, spelled as the annotation spells them.
            scope: The page being rendered. It is never linked, so a class's own signature and
                attributes do not link back to the page you are already reading.

        Returns:
            The pairs that were found, or `None` when there are none. `None` rather than an empty
            mapping, so the caller can leave the prop off the element entirely.
        """

        found = {
            name: self._routes[name] for name in types if name in self._routes and name != scope
        }

        return found or None


def expand_self(path: str, scope: str | None) -> str:
    """Replace a leading `self` with the page it stands for, in a link target or its label alike.

    Args:
        path: A name that may begin with `self`.
        scope: The page being rendered, when there is one.

    Returns:
        The name with `self` replaced, or unchanged when there is nothing to replace it with.
    """

    if scope and _is_self_path(path):
        return scope + path[len("self") :]

    return path


def _is_self_path(path: str) -> bool:
    return path == "self" or path.startswith("self.")


def _spellings(module_path: Sequence[str], name: str) -> list[str]:
    """Every way a docstring might write `name`, from fully qualified down to bare.

    Docstrings reference a symbol by its import path about as often as by its short name, so
    `example.core.Client` has to resolve as readily as `Client`. Each partial suffix is recorded
    too, since half-qualified references are common.
    """

    return [".".join([*module_path[index:], name]) for index in range(len(module_path) + 1)]


def _collect(module: griffe.Module, prefix: list[str], config: Config) -> dict[str, str]:
    routes: dict[str, str] = {}
    path = [*prefix, module.name]
    page = config.href(path)

    # module attributes and functions are rendered on the module's own page, each under an anchor
    # named after it. registering them is what lets a type alias resolve from inside a signature.
    anchored = [
        *(attribute.name for attribute in module_attributes(module, config)),
        *(function.name for function in public_members(module, griffe.Kind.FUNCTION, config)),
    ]
    for name in anchored:
        for spelling in _spellings(path, name):
            # setdefault leaves the name free for a class below, which owns a whole page and is
            # the better target when both spell the same name
            _ = routes.setdefault(spelling, f"{page}#{name}")

    for cls in public_members(module, griffe.Kind.CLASS, config):
        base = [*path, cls.name]
        class_page = config.href(base)
        owners = _spellings(path, cls.name)
        routes.update({name: class_page for name in owners})
        routes.update(_anchors(cls, class_page, owners, config))

        # the renderer nests exactly one level deep, so these are the only nested classes with
        # pages of their own. going deeper here would mint links to files nobody writes.
        for nested in cls.members.values():
            if nested.kind is not griffe.Kind.CLASS or nested.name.startswith("_"):
                continue

            if config.excludes(nested):
                continue

            nested_page = config.href([*base, nested.name])
            names = [nested.name, *(f"{owner}.{nested.name}" for owner in owners)]
            routes.update({name: nested_page for name in names})
            routes.update(_anchors(nested, nested_page, names, config))

    for submodule in public_members(module, griffe.Kind.MODULE, config):
        # the submodule's own page, so prose can point at the module and not only at what is in it
        for spelling in _spellings(path, submodule.name):
            _ = routes.setdefault(spelling, config.href([*path, submodule.name]))

        routes.update(_collect(cast(griffe.Module, submodule), path, config))

    return routes


def _anchors(
    owner: griffe.Object | griffe.Alias,
    page: str,
    owner_names: Sequence[str],
    config: Config,
) -> dict[str, str]:
    """`Owner.member` to that member's anchor on `page`, for every spelling of the owner.

    A nested class answers to both `Options` and `Client.Options`, so its members have to answer
    to both too.
    """

    routes: dict[str, str] = {}
    for member in owner.members.values():
        if member.name.startswith("_") or config.excludes(member):
            continue

        if member.kind in _ANCHORED_KINDS:
            for name in owner_names:
                routes[f"{name}.{member.name}"] = f"{page}#{member.name}"

    return routes
