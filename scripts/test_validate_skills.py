#!/usr/bin/env python3
"""Тесты валидатора библиотеки навыков.

Проверяют не «проходит ли чистый репозиторий» (это ничего не доказывает), а то,
что валидатор ловит поломки: каждый кейс ломает копию репозитория одним
способом и ждёт находку нужного уровня.

    python scripts/test_validate_skills.py

Мутации выполняются только во временных копиях; рабочий репозиторий защищён
предохранителем `guard()`. Только стандартная библиотека.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPTS)
REPO_KEY = os.path.normcase(REPO)
VALIDATOR = os.path.join("scripts", "validate_skills.py")

MUTATIONS: list[tuple[str, object, str, str]] = []


def guard(path: str) -> None:
    """Предохранитель: любая мутация вне временной копии — немедленный отказ."""
    if os.path.normcase(os.path.abspath(path)) == REPO_KEY:
        raise SystemExit("ОТКАЗ: попытка мутировать рабочий репозиторий")


def mutation(name: str, level: str = "ERROR", needle: str = ""):
    def deco(fn):
        MUTATIONS.append((name, fn, level, needle))
        return fn
    return deco


# --- вспомогательное ------------------------------------------------------

def run(args: list[str], cwd: str, check: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if check and proc.returncode:
        raise SystemExit(f"команда упала: {args}\n{proc.stdout}\n{proc.stderr}")
    return proc


def validate(work: str, *extra: str) -> tuple[int, str]:
    guard(work)
    proc = run([sys.executable, os.path.join(work, VALIDATOR), *extra], work)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def git(work: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    guard(work)
    return run(["git", "-C", work, "-c", "user.email=t@t", "-c", "user.name=t", *args],
               work, check=check)


def edit(work: str, rel: str, fn) -> None:
    guard(work)
    path = os.path.join(work, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(fn(text))


def skills_of(work: str) -> list[str]:
    return sorted(d for d in os.listdir(work)
                  if os.path.isfile(os.path.join(work, d, "SKILL.md")))


def plugin_version(work: str) -> str:
    with open(os.path.join(work, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
        return json.load(fh)["version"]


def skill_version(work: str, skill: str) -> str:
    with open(os.path.join(work, skill, "SKILL.md"), encoding="utf-8") as fh:
        return re.search(r"^\s*version:\s*(\S+)$", fh.read(), re.M).group(1)


def bump_plugin(work: str, new: str) -> None:
    old = plugin_version(work)
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        edit(work, rel, lambda t: t.replace(f'"version": "{old}"', f'"version": "{new}"'))


# --- мутации: фронтматтер --------------------------------------------------

@mutation("описание длиннее 1024", needle="символов — лимит")
def _(work):
    # Описание заменяется целиком: у части навыков это однострочный скаляр,
    # у части — свёрнутый блок, и дописывать строку вслепую нельзя.
    skill = skills_of(work)[0]
    long_desc = ("description: >\n  " + "очень длинное описание навыка " * 40
                 + "\n  Используй когда прогоняешь тесты валидатора.\n")
    edit(work, f"{skill}/SKILL.md",
         lambda t: re.sub(r"^description:.*?(?=^metadata:)", long_desc, t,
                          count=1, flags=re.S | re.M))


@mutation("name не совпадает с папкой", needle="не совпадает с именем папки")
def _(work):
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md", lambda t: t.replace(f"name: {skill}", "name: wrong-name", 1))


@mutation("посторонний ключ фронтматтера", needle="неизвестный ключ фронтматтера")
def _(work):
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md", lambda t: t.replace("\nmetadata:", "\nauthor: someone\nmetadata:", 1))


@mutation("посторонний ключ metadata", needle="неизвестный ключ metadata")
def _(work):
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md", lambda t: t.replace("\nmetadata:", "\nmetadata:\n  owner: me", 1))


@mutation("версия не semver", needle="не semver")
def _(work):
    skill = skills_of(work)[0]
    current = skill_version(work, skill)
    edit(work, f"{skill}/SKILL.md", lambda t: t.replace(f"version: {current}", "version: 1.2", 1))


@mutation("личный путь с логином в навыке", needle="домашний путь с логином")
def _(work):
    # Путь собирается из частей: иначе сам файл теста попадёт под эту же проверку.
    leak = "C:" + chr(92) + "Users" + chr(92) + "vasiliy" + chr(92) + "notes"
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md", lambda t: t + f"\nПример: положи файл в {leak}\n")


@mutation("привязка инструкции к ОС пользователя", level="WARN",
          needle="утверждение о среде пользователя")
def _(work):
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md",
         lambda t: t + "\nМашина пользователя — Windows/PowerShell, команды под неё.\n")


@mutation("размер команды подан как данность", level="WARN",
          needle="размер команды подан как данность")
def _(work):
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md",
         lambda t: t + "\nПрофиль владельца — соло-разработчик с агентами.\n")


@mutation("строка описания оборвана на дефисе", needle="оборвана на дефисе")
def _(work):
    skill = skills_of(work)[0]
    broken = ("description: >\n  Навык про сервер, подробности смотри в vps-\n"
              "  ops и рядом. Используй когда тестируешь валидатор.\n")
    edit(work, f"{skill}/SKILL.md",
         lambda t: re.sub(r"^description:.*?(?=^metadata:)", broken, t,
                          count=1, flags=re.S | re.M))


@mutation("описание без условий срабатывания", level="WARN", needle="нет условий срабатывания")
def _(work):
    skill = skills_of(work)[0]
    edit(work, f"{skill}/SKILL.md",
         lambda t: re.sub(r"^description:.*?(?=^metadata:)", "description: Делает нечто полезное.\n",
                          t, count=1, flags=re.S | re.M))


# --- мутации: ссылки и структура -------------------------------------------

@mutation("битая ссылка на references/", needle="отсутствующий")
def _(work):
    for skill in skills_of(work):
        refs = os.path.join(work, skill, "references")
        if os.path.isdir(refs):
            files = sorted(os.listdir(refs))
            if files:
                os.remove(os.path.join(refs, files[0]))
                return
    raise SystemExit("не найдено навыка с references/")


@mutation("осиротевший файл в references/", level="WARN", needle="осиротевший")
def _(work):
    for skill in skills_of(work):
        refs = os.path.join(work, skill, "references")
        if os.path.isdir(refs):
            with open(os.path.join(refs, "ghost.md"), "w", encoding="utf-8") as fh:
                fh.write("никто на меня не ссылается\n")
            return
    raise SystemExit("не найдено навыка с references/")


@mutation("посторонний .md в корне навыка", needle="в корне навыка")
def _(work):
    skill = skills_of(work)[0]
    with open(os.path.join(work, skill, "REFERENCE.md"), "w", encoding="utf-8") as fh:
        fh.write("старая конвенция\n")


# --- мутации: README и манифесты -------------------------------------------

@mutation("навык пропал из каталога README", needle="отсутствует в каталоге")
def _(work):
    skill = skills_of(work)[-1]
    edit(work, "README.md", lambda t: t.replace(f"[`{skill}`]({skill}/)", skill))


@mutation("устаревший бейдж README", needle="бейдж обещает")
def _(work):
    count = len(skills_of(work))
    edit(work, "README.md", lambda t: t.replace(f"skills-{count}-", f"skills-{count - 4}-", 1))


@mutation("новый навык не внесён в README", needle="отсутствует в каталоге")
def _(work):
    path = os.path.join(work, "zzz-new-skill")
    os.makedirs(path)
    with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write("---\nname: zzz-new-skill\ndescription: Тестовый навык. "
                 "Используй когда прогоняешь тесты валидатора.\nmetadata:\n  version: 1.0.0\n---\n\n# Test\n")


@mutation("версии манифестов разошлись", needle="версии разошлись")
def _(work):
    old = plugin_version(work)
    edit(work, ".claude-plugin/plugin.json",
         lambda t: t.replace(f'"version": "{old}"', '"version": "9.9.9"'))


@mutation("устаревшее число навыков в marketplace", needle="навыков, фактически")
def _(work):
    count = len(skills_of(work))
    edit(work, ".claude-plugin/marketplace.json",
         lambda t: t.replace(f"{count} Agent Skills", f"{count - 2} Agent Skills", 1))


# --- прогон мутаций --------------------------------------------------------

def run_mutations(clean: str, base: str) -> int:
    fails = 0
    for name, mutate, level, needle in MUTATIONS:
        work = os.path.join(base, "mut-" + re.sub(r"\W+", "-", name).strip("-")[:40])
        shutil.copytree(clean, work)
        mutate(work)
        code, out = validate(work)
        strict_code, _ = validate(work, "--strict")
        found = f"{level:6}" in out and needle in out
        # ERROR валит сразу; WARN валит только под --strict.
        expected_code = 1 if level == "ERROR" else 0
        ok = found and code == expected_code and strict_code == 1
        fails += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:44} {level:5} exit={code} strict={strict_code}")
        if not ok:
            print("\n".join("         " + l for l in out.strip().splitlines()[:8]))
        shutil.rmtree(work, ignore_errors=True)
    return fails


# --- прогон проверок бампа версий ------------------------------------------

def run_bump(base: str) -> int:
    clone = os.path.join(base, "clone")
    proc = run(["git", "clone", "--quiet", "--no-hardlinks", "--local", REPO, clone], base)
    if proc.returncode:
        print("  [SKIP] git clone недоступен — проверки бампа пропущены")
        print("\n".join("         " + l for l in (proc.stderr or "").strip().splitlines()[:4]))
        return 0
    guard(clone)

    os.makedirs(os.path.join(clone, "scripts"), exist_ok=True)
    for name in ("validate_skills.py", "test_validate_skills.py"):
        src = os.path.join(SCRIPTS, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(clone, "scripts", name))
    git(clone, "add", "-A")
    # --allow-empty: если скрипты уже закоммичены, копирование не даёт изменений,
    # а baseline-коммит нужен только как база для сравнения версий.
    git(clone, "commit", "-q", "--allow-empty", "-m", "baseline")
    git(clone, "branch", "-f", "base-ref", "HEAD")

    skill = skills_of(clone)[0]
    fails = 0

    def check(label, args, want_error, needle=""):
        nonlocal fails
        code, out = validate(clone, "--check-bump", *args)
        found = ("ERROR" in out and needle in out) if want_error else ("ERROR" not in out)
        ok = found and (code == 1) == want_error
        fails += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:44} exit={code}")
        if not ok:
            print("\n".join("         " + l for l in out.strip().splitlines()[:8]))
        return out

    edit(clone, f"{skill}/SKILL.md", lambda t: t + "\nправка\n")
    git(clone, "commit", "-qam", "edit skill")
    check("навык изменён, версии не бампнуты", ["--base", "base-ref"], True, "версия плагина осталась")

    old_skill_ver = skill_version(clone, skill)
    edit(clone, f"{skill}/SKILL.md",
         lambda t: t.replace(f"version: {old_skill_ver}", "version: 9.9.9", 1))
    git(clone, "commit", "-qam", "bump skill only")
    check("бампнут навык, плагин — нет", ["--base", "base-ref"], True, "версия плагина осталась")

    bump_plugin(clone, "9.9.9")
    git(clone, "commit", "-qam", "bump plugin")
    check("обе версии бампнуты — чисто", ["--base", "base-ref"], False)

    git(clone, "branch", "-f", "ref-base", "HEAD")
    for candidate in skills_of(clone):
        refs = os.path.join(clone, candidate, "references")
        if os.path.isdir(refs) and os.listdir(refs):
            rel = f"{candidate}/references/{sorted(os.listdir(refs))[0]}"
            edit(clone, rel, lambda t: t + "\nдобавка\n")
            break
    git(clone, "commit", "-qam", "edit reference only")
    out = check("правка только references — нужен бамп плагина",
                ["--base", "ref-base"], True, "версия плагина осталась")
    if "metadata.version` остался" in out:
        print("         FAIL: бамп самого навыка не должен требоваться")
        fails += 1

    code, out = validate(clone, "--check-bump", "--base", "no-such-ref-xyz")
    loud = "не найдена" in out and "сравниваю с" in out
    fails += not loud
    print(f"  [{'PASS' if loud else 'FAIL'}] {'нерезолвящаяся база названа вслух':44}")

    code, out = validate(clone, "--check-bump", "--base", "0" * 40)
    quiet = "не найдена" not in out
    fails += not quiet
    print(f"  [{'PASS' if quiet else 'FAIL'}] {'нулевая база (новая ветка) — тихий откат':44}")

    return fails


def main() -> int:
    base = tempfile.mkdtemp(prefix="llm-skills-tests-")
    clean = os.path.join(base, "clean")
    shutil.copytree(REPO, clean, ignore=shutil.ignore_patterns(".git", ".claude", "__pycache__"))

    code, out = validate(clean)
    print(f"базовый прогон на чистой копии: exit={code}")
    if code != 0:
        print(out)
        shutil.rmtree(base, ignore_errors=True)
        return 1

    print("\nмутации:")
    fails = run_mutations(clean, base)
    print("\nбамп версий:")
    fails += run_bump(base)

    shutil.rmtree(base, ignore_errors=True)
    total = len(MUTATIONS) + 6
    print(f"\nпровалено: {fails} из ~{total}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
