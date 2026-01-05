"""CodeWarden Framework Middleware.

This module provides middleware integrations for various web frameworks.
Install the appropriate extras to use framework-specific middleware:

    pip install codewarden[fastapi]
    pip install codewarden[flask]
    pip install codewarden[django]

Example (FastAPI):
    >>> from fastapi import FastAPI
    >>> from codewarden.middleware import FastAPIMiddleware
    >>>
    >>> app = FastAPI()
    >>> app.add_middleware(FastAPIMiddleware)
"""

from __future__ import annotations

from codewarden.middleware.base import BaseMiddleware

__all__ = ["BaseMiddleware"]

# Conditionally import FastAPI middleware
try:
    from codewarden.middleware.fastapi import (
        CodeWardenMiddleware as FastAPIMiddleware,
    )

    __all__.append("FastAPIMiddleware")
except ImportError:
    # FastAPI/Starlette not installed
    FastAPIMiddleware = None  # type: ignore[misc, assignment]
