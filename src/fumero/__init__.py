"""Turn a Python module into a Fumadocs API reference."""

from . import error, model
from .config import Config, Dialect
from .link import LinkTable
from .mdx import encode_text
from .parse import load_module

__all__ = ["Config", "Dialect", "LinkTable", "encode_text", "error", "load_module", "model"]
