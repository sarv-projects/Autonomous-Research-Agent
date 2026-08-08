"""Web dashboard for the LLM gateway. Run with: ``python -m src.dashboard``."""

from .server import serve, main

__all__ = ["serve", "main"]
