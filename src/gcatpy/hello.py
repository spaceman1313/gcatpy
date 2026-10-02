"""Placeholder greeting used to verify that gcatpy installs, imports, and runs.

This module exists only to exercise the packaging and tooling pipeline (import,
``python -m gcatpy``, type checking, tests, CI). Remove it once real functionality
lands.
"""

DEFAULT_NAME = "world"


def greet(name: str = DEFAULT_NAME) -> str:
    """Build a greeting for ``name``.

    Args:
        name: Who to greet. Leading and trailing whitespace is stripped; a blank
            value falls back to ``DEFAULT_NAME``.

    Returns:
        The greeting, e.g. ``"Hello, world! (gcatpy)"``.

    Examples:
        >>> greet()
        'Hello, world! (gcatpy)'
        >>> greet("  Sputnik ")
        'Hello, Sputnik! (gcatpy)'
    """
    cleaned = name.strip() or DEFAULT_NAME
    return f"Hello, {cleaned}! (gcatpy)"
