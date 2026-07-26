"""Turn a Python module into a Fumadocs API reference."""

from . import error, model
from .config import Config, Dialect
from .parse import load_module

__all__ = ["Config", "Dialect", "error", "load_module", "model"]
