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

__all__ = ["load_module", "remove_prefix"]

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


def remove_prefix(text: str) -> str:
    """Strip dotted module paths from type references (e.g. `pathlib.Path` → `Path`), relying on
    the python convention that classes are CapitalCase.
    """

    return _MODULE_PREFIX_RE.sub(r"\1", text.replace("builtins.", ""))
