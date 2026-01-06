"""CodeWarden Framework Middleware.

This module provides middleware integrations for various web frameworks.
Install the appropriate extras to use framework-specific middleware:

    pip install codewarden[fastapi]
    pip install codewarden[flask]
    pip install codewarden[django]

Example (FastAPI):
    >>> from fastapi import FastAPI
    >>> from codewarden.middleware import FastAPIMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(FastAPIMiddleware)

Example (Flask):
    >>> from flask import Flask
    >>> from codewarden.middleware import init_flask
    >>> app = Flask(__name__)
    >>> init_flask(app)

Example (Django):
    Add 'codewarden.middleware.django.DjangoMiddleware' to MIDDLEWARE
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

# Conditionally import Flask middleware
try:
    from codewarden.middleware.flask import FlaskMiddleware, init_flask

    __all__.extend(["FlaskMiddleware", "init_flask"])
except ImportError:
    # Flask not installed
    FlaskMiddleware = None  # type: ignore[misc, assignment]
    init_flask = None  # type: ignore[misc, assignment]

# Conditionally import Django middleware
try:
    from codewarden.middleware.django import DjangoMiddleware

    __all__.append("DjangoMiddleware")
except ImportError:
    # Django not installed
    DjangoMiddleware = None  # type: ignore[misc, assignment]
