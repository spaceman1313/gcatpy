"""Command-line entry point: ``python -m gcatpy [NAME]``.

Prints a greeting and the installed gcatpy version. Placeholder until real commands
exist; see :mod:`gcatpy.hello`.
"""

import argparse
import sys
from collections.abc import Sequence

from gcatpy import __version__
from gcatpy.hello import DEFAULT_NAME, greet


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the ``gcatpy`` command.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="python -m gcatpy",
        description="gcatpy placeholder command: prints a greeting.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=DEFAULT_NAME,
        help=f"who to greet (default: {DEFAULT_NAME})",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command.

    Args:
        argv: Arguments excluding the program name. ``None`` reads ``sys.argv[1:]``.

    Returns:
        Process exit status (``0`` on success).
    """
    args = build_parser().parse_args(argv)
    print(greet(args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
