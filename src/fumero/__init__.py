"""Turn a Python module into a Fumadocs API reference."""

from . import error, model
from .component import component_source, init
from .config import Config, Dialect
from .link import LinkTable
from .mdx import encode_text
from .parse import load_module
from .render import Renderer, Result, UnresolvedLink, generate

__all__ = [
    "Config",
    "Dialect",
    "LinkTable",
    "Renderer",
    "Result",
    "UnresolvedLink",
    "component_source",
    "encode_text",
    "error",
    "generate",
    "init",
    "load_module",
    "model",
]
