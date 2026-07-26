"""Read a Python module with griffe and describe it in [`fumero.model`] terms.

This is the only part of fumero that knows griffe exists. Everything downstream works from the
model, so a change in how a module is introspected never reaches the output.

Start at [`load_module`], which reads a module and hands back the tree the rest of this module
takes apart.
"""

import re
from typing import cast

import griffe

from .config import Config
from .error import ModuleNotFound
from .model import Property

__all__ = ["load_module", "module_attributes", "public_members", "remove_prefix"]

_MODULE_PREFIX_RE = re.compile(r"(?:[a-z_][a-z0-9_]*\.)+([A-Z][A-Za-z0-9_]*)")


def load_module(name: str, config: Config | None = None) -> griffe.Module:
    """Read a module and hand back griffe's view of it.

    A package is a module that happens to hold other modules, so either will do: `example` reads
    the whole package, `example.core` reads that subtree on its own.

    Args:
        name: An importable module path.
        config: Supplies the docstring dialect. Defaults are used when this is `None`.

    Returns:
        The module, and everything under it.

    Raises:
        ModuleNotFound: `name` is not importable from here.

    Examples:
        ```python
        module = load_module("example")
        ```
    """

    config = config or Config()
    try:
        loaded = griffe.load(name, docstring_parser=griffe.Parser(config.dialect))
    except ImportError as error:
        raise ModuleNotFound(name) from error

    return cast(griffe.Module, loaded)


def public_members(
    module: griffe.Module, kind: griffe.Kind, config: Config
) -> list[griffe.Object | griffe.Alias]:
    """The members of `module` of one kind that belong in the documentation.

    `__all__` decides what is public. A module that defines one is taken at its word; a module that
    does not falls back to the convention that a leading underscore means private.

    Args:
        module: The module to look through.
        kind: The kind of member to collect, such as `griffe.Kind.CLASS`.
        config: Supplies the exclude patterns.

    Returns:
        The matching members, in the order the module declares them.
    """

    exports = None if module.exports is None else {str(export) for export in module.exports}

    def is_public(name: str, member: griffe.Object | griffe.Alias) -> bool:
        exported = not name.startswith("_") if exports is None else name in exports

        return exported and not config.excludes(member)

    return [
        member
        for name, member in module.members.items()
        if member.kind is kind and is_public(name, member)
    ]


def module_attributes(module: griffe.Module, config: Config) -> list[Property]:
    """The module's public attributes, sorted by name.

    Type aliases are attributes as far as griffe is concerned, which is what lets a signature link
    to one.

    Args:
        module: The module to look through.
        config: Supplies the exclude patterns.

    Returns:
        One [`fumero.model.Property`] per attribute.
    """

    attributes = [
        _attribute_property(attribute)
        for attribute in module.attributes.values()
        if not attribute.name.startswith("_") and not config.excludes(attribute)
    ]

    return sorted(attributes, key=lambda attribute: attribute.name)


def _attribute_property(attribute: griffe.Attribute, description: str | None = None) -> Property:
    annotation = (
        remove_prefix(str(attribute.annotation)) if attribute.annotation is not None else None
    )
    value = str(attribute.value) if attribute.value is not None else None

    return Property(attribute.name, annotation, description, value)


def remove_prefix(text: str) -> str:
    """Strip dotted module paths from type references (e.g. `pathlib.Path` → `Path`), relying on
    the python convention that classes are CapitalCase.
    """

    return _MODULE_PREFIX_RE.sub(r"\1", text.replace("builtins.", ""))
