"""Turn a Python module into a Fumadocs API reference."""

from . import error, model
from .config import Config, Dialect
from .link import LinkTable
from .parse import load_module

__all__ = ["Config", "Dialect", "LinkTable", "error", "load_module", "model"]
