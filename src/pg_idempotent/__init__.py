"""PostgreSQL Idempotent Migration Tool."""
__version__ = "0.1.0"

from .transformer.transformer import SQLTransformer
from .cli import app, main

__all__ = ["SQLTransformer", "app", "main"]
