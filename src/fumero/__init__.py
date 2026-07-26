"""Turn a Python module into a Fumadocs API reference."""

from . import error, model
from .config import Config, Dialect

__all__ = ["Config", "Dialect", "error", "model"]
