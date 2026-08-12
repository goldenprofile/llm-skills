#!/usr/bin/env python3
"""Роутинг-eval: срабатывает ли нужный навык на реальных запросах пользователя.

Меряет не качество работы навыка, а маршрутизацию — то единственное, за что
отвечает `description`: увидев запрос, потянется ли модель за навыком и за
правильным ли. Кейсы в `evals/routing-cases.jsonl` — обезличенные формулировки
из реальной работы, а не придуманные под удобный ответ.

    python scripts/run_routing_eval.py --dry-run        # список кейсов, без затрат
    python scripts/run_routing_eval.py --tier 1         # прогон подмножества
    python scripts/run_routing_eval.py --model sonnet   # весь набор

Каждый кейс — отдельная сессия `claude -p` в одноразовой песочнице с
запрещёнными инструментами: модель может либо вызвать навык, либо ответить
текстом. Правки, сеть и сабагенты отключены, файлы проекта не затрагиваются.
Прогон стоит денег: цена каждого кейса печатается, итог — в конце.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(REPO, "evals", "routing-cases.jsonl")

# Модель должна решить «навык или нет» сразу: разведка по файлам к маршрутизации
# отношения не имеет, а стоит денег и размывает результат.
BLOCKED = ("Bash Edit Write Read Grep Glob NotebookEdit WebFetch WebSearch "
           "Agent Task ToolSearch AskUserQuestion")


def load_cases(tier: int | None) -> list[dict]:
    cases = []
    with open(CASES, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                case = json.loads(line)
                if tier is None or case.get("tier") == tier:
                    cases.append(case)
    return cases


def run_case(case: dict, model: str, sandbox: str) -> dict:
    cmd = [
        "claude", "-p", case["prompt"],
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "plan",
        "--plugin-dir", REPO,
        "--disallowedTools", BLOCKED,
        # MCP-серверы к маршрутизации навыков отношения не имеют, но раздувают
        # системный промт и удорожают каждый кейс.
        "--strict-mcp-config",
        "--model", model,
    ]
    proc = subprocess.run(cmd, cwd=sandbox, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=600)
    fired, cost, text = [], 0.0, ""
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") == "assistant":
            for block in rec.get("message", {}).get("content", []) or []:
                if block.get("type") == "tool_use" and block.get("name") == "Skill":
                    skill = (block.get("input") or {}).get("skill", "")
                    fired.append(skill.split(":")[-1])
                elif block.get("type") == "text":
                    text += block.get("text", "")
        elif rec.get("type") == "result":
            cost = rec.get("total_cost_usd") or 0.0
    return {"fired": fired, "cost": cost, "text": text.strip()}


def verdict(case: dict, fired: list[str]) -> str:
    expect = case.get("expect") or []
    first = fired[0] if fired else None
    if not expect:
        return "OK" if not fired else "ЛОЖНОЕ"       # навык не нужен
    if first is None:
        return "МОЛЧИТ"                              # нужен, но не сработал
    return "OK" if first in expect else "НЕ ТОТ"


def main() -> int:
    ap = argparse.ArgumentParser(description="Роутинг-eval библиотеки навыков")
    ap.add_argument("--model", default="sonnet", help="модель для прогона (по умолчанию sonnet)")
    ap.add_argument("--tier", type=int, help="прогнать только кейсы этого уровня")
    ap.add_argument("--limit", type=int, help="ограничить число кейсов")
    ap.add_argument("--dry-run", action="store_true", help="показать кейсы, ничего не запускать")
    ap.add_argument("--out", help="файл для записи результатов (jsonl)")
    args = ap.parse_args()

    cases = load_cases(args.tier)
    if args.limit:
        cases = cases[:args.limit]
    if not cases:
        print("нет кейсов под фильтр", file=sys.stderr)
        return 1

    if args.dry_run:
        for case in cases:
            exp = ", ".join(case["expect"]) if case["expect"] else "(навык не нужен)"
            print(f"{case['id']:26} -> {exp}\n{'':26}    {case['prompt'][:110]}")
        print(f"\nкейсов: {len(cases)}; прогон обойдётся примерно "
              f"в ${0.10 * len(cases):.2f}–${0.40 * len(cases):.2f}")
        return 0

    sandbox = tempfile.mkdtemp(prefix="routing-eval-")
    # Минимальный Django-проект: скилам есть на что смотреть, но ничего ценного
    # в песочнице нет.
    os.makedirs(os.path.join(sandbox, "apps", "core", "migrations"), exist_ok=True)
    os.makedirs(os.path.join(sandbox, "config"), exist_ok=True)
    for rel, body in (
        ("manage.py", "import os, sys\nif __name__ == '__main__':\n    pass\n"),
        ("config/settings.py", "DEBUG = True\nINSTALLED_APPS = ['apps.core']\n"),
        ("apps/core/models.py", "from django.db import models\n"),
        ("requirements.txt", "Django==5.1\ngunicorn==22.0.0\n"),
    ):
        with open(os.path.join(sandbox, rel), "w", encoding="utf-8") as fh:
            fh.write(body)

    results, total = [], 0.0
    counts = {"OK": 0, "МОЛЧИТ": 0, "НЕ ТОТ": 0, "ЛОЖНОЕ": 0}
    print(f"кейсов: {len(cases)} | модель: {args.model} | песочница: {sandbox}\n", flush=True)
    for i, case in enumerate(cases, 1):
        try:
            res = run_case(case, args.model, sandbox)
        except subprocess.TimeoutExpired:
            res = {"fired": [], "cost": 0.0, "text": "(таймаут)"}
        mark = verdict(case, res["fired"])
        counts[mark] += 1
        total += res["cost"]
        got = ", ".join(res["fired"]) if res["fired"] else "—"
        exp = ", ".join(case["expect"]) if case["expect"] else "—"
        # flush: прогон долгий, вывод должен идти по мере готовности кейсов
        print(f"[{mark:7}] {i:2}/{len(cases)} {case['id']:26} ждали: {exp:34} "
              f"сработало: {got:26} ${res['cost']:.3f}", flush=True)
        results.append({**case, **res, "verdict": mark})

    shutil.rmtree(sandbox, ignore_errors=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            for row in results:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"\nрезультаты записаны: {args.out}")

    hit = counts["OK"]
    print(f"\nитог: {hit}/{len(cases)} верно "
          f"({100 * hit / len(cases):.0f}%) | молчит: {counts['МОЛЧИТ']} | "
          f"не тот: {counts['НЕ ТОТ']} | ложное срабатывание: {counts['ЛОЖНОЕ']}")
    print(f"стоимость прогона: ${total:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
