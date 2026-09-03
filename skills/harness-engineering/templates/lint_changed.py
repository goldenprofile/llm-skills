#!/usr/bin/env python3
"""PostToolUse-хук: линтит ровно тот Python-файл, который агент только что изменил.

Копируется в проект как `.claude/hooks/lint_changed.py` и вызывается из
`.claude/settings.json`:

    {"type": "command", "command": "python .claude/hooks/lint_changed.py"}

Только стандартная библиотека: ни `jq`, ни shell-конструкций — на Windows и на
POSIX поведение одинаковое. Линтер ищется сам: `ruff` в PATH, иначе `uv run ruff`;
переопределяется переменной `HARNESS_RUFF` (например `HARNESS_RUFF="poetry run ruff"`).

Коды выхода (контракт PostToolUse):
  0 — файл чистый, не Python, исключён настройками проекта или линтер недоступен;
  2 — есть замечания; stderr уходит агенту как обратная связь.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

SUFFIXES = (".py", ".pyi")
TIMEOUT_S = 30
RUFF_FOUND_ISSUES = 1  # 0 — чисто, 1 — есть находки, 2 — ошибка самого ruff


def runner() -> list[str] | None:
    """Как звать ruff в этом проекте. None — линтера нет, хук молча пропускает."""
    override = os.environ.get("HARNESS_RUFF")
    if override:
        return override.split()
    if shutil.which("ruff"):
        return ["ruff"]
    if shutil.which("uv"):
        return ["uv", "run", "--quiet", "ruff"]
    return None


def changed_python_file(payload: dict) -> str | None:
    tool_input = payload.get("tool_input")
    path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(path, str) or not path.endswith(SUFFIXES):
        return None
    return path if os.path.isfile(path) else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, UnicodeDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0

    path = changed_python_file(payload)
    cmd = runner()
    if path is None or cmd is None:
        return 0

    try:
        # --force-exclude: уважать exclude из pyproject даже для явно переданного
        # пути (иначе линтуются миграции и прочее, что проект исключил осознанно).
        proc = subprocess.run(
            [*cmd, "check", "--quiet", "--force-exclude", path],
            capture_output=True, text=True, timeout=TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return 0

    # Только код 1 — это находки. Всё остальное (нет ruff в окружении, сломанный
    # конфиг) не должно выглядеть как проваленный линт.
    if proc.returncode != RUFF_FOUND_ISSUES or not proc.stdout.strip():
        return 0

    sys.stderr.write(proc.stdout)
    return 2


if __name__ == "__main__":
    sys.exit(main())
