"""Claude Code PostToolUse hook: format and lint a Python file Claude edited.

Reads the hook event JSON from stdin. If the edited file is a ``.py`` file,
runs ``ruff format`` on it, then ``ruff check`` without ``--fix``, so lint
fixes stay visible in the diff rather than being applied silently. Any lint
errors are written to stderr with exit code 2, which Claude Code feeds back
to Claude so it fixes them, as a reviewable edit, in the same turn.

See https://code.claude.com/docs/en/hooks-guide for the event schema and
exit-code semantics.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BLOCKING_EXIT_CODE = 2


def _edited_path(event: object) -> Path | None:
    """Return the edited file path from a hook event, if there is one.

    Args:
        event: Parsed PostToolUse event payload.

    Returns:
        The edited file's path, or ``None`` if the event has no file path.
    """
    if not isinstance(event, dict):
        return None
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    file_path = tool_input.get("file_path")
    return Path(file_path) if isinstance(file_path, str) else None


def _ruff(*args: str) -> subprocess.CompletedProcess[str]:
    """Run ruff through uv and capture its output.

    Args:
        *args: Arguments passed to ``ruff``.

    Returns:
        The completed process, with stdout and stderr captured as text.
    """
    return subprocess.run(
        ["uv", "run", "--quiet", "ruff", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    """Format the edited file and report lint issues without fixing them.

    Returns:
        0 when there is nothing to do or the file is lint-clean; 2 when lint
        issues remain.
    """
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    path = _edited_path(event)
    if path is None or path.suffix != ".py" or not path.is_file():
        return 0

    _ruff("format", str(path))
    result = _ruff("check", "--output-format=concise", str(path))
    if result.returncode != 0:
        sys.stderr.write(f"ruff found lint issues in {path}:\n{result.stdout}")
        return BLOCKING_EXIT_CODE
    return 0


if __name__ == "__main__":
    sys.exit(main())
