"""Forced-Reasoning protocol reproduction (arXiv:2609.26637)."""

from .client import ResponsesClient
from .prompts import DESC_DEFAULT, DESC_MAXIMAL, DESC_THINK_HERE, make_tool
from .protocol import run_session

__all__ = [
    "ResponsesClient",
    "DESC_DEFAULT",
    "DESC_MAXIMAL",
    "DESC_THINK_HERE",
    "make_tool",
    "run_session",
]
