#!/usr/bin/env python3
"""Валидатор библиотеки навыков llm-skills.

Проверяет инварианты, которые иначе держатся только на дисциплине:
фронтматтер, лимит описания, целостность ссылок на references/,
синхронность README с составом репозитория, манифесты плагина и
бамп версий при изменении навыков.

Только стандартная библиотека — запускается без venv:

    python scripts/validate_skills.py
    python scripts/validate_skills.py --list
    python scripts/validate_skills.py --strict --check-bump

Код возврата: 0 — чисто, 1 — есть ошибки (или предупреждения при --strict).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- контракт фронтматтера -------------------------------------------------

FM_TOP_KEYS = {"name", "description", "metadata", "allowed-tools", "license"}
FM_REQUIRED = {"name", "description"}
FM_METADATA_KEYS = {"version", "verified"}

DESC_MAX = 1024          # лимит валидации Anthropic
DESC_WARN = 900          # запас, чтобы правки не выталкивали за лимит
NAME_MAX = 64
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Тело грузится в контекст целиком при срабатывании навыка.
BODY_WARN_LINES = 150
BODY_WARN_BYTES = 8 * 1024

# Описание должно называть условия срабатывания, а не только назначение.
TRIGGER_MARKERS = ("использу", "вызывается", "триггер", "use when", "используй")

# Навыки, привязанные к версии внешнего инструмента или к поведению Claude Code:
# у них metadata.verified протухает быстрее всего.
VERSION_FRAGILE = {
    "advanced-seo-optimizer", "aiogram-bot-auditor", "claude-code-auditor",
    "context-hygiene", "dependency-auditor", "django-tailwind-optimizer",
    "fastapi-architect", "goal-pipeline", "google-discover-optimize",
    "llm-delegation", "llm-feature-architect", "ratchet-loop",
}
VERIFIED_STALE_DAYS = 180

REF_PATH_RE = re.compile(r"(?:^|[\s(`\[])((?:\./)?references/[\w\-./]+\.md)")

# Репозиторий публичный: домашние пути с конкретным логином выдают владельца и
# структуру его машины. Разрешены только обезличенные плейсхолдеры.
HOME_PATH_RE = re.compile(r"(?:[Cc]:\\+Users\\+|/home/|/Users/)([A-Za-z][\w.-]*)")
HOME_PLACEHOLDERS = {"user", "username", "youruser", "deploy", "app", "me",
                     "name", "yourname", "developer"}

# Библиотеку ставят себе на другой ОС и в другом ассистенте. Утверждение о среде
# как о факте («машина пользователя — Windows») на чужой машине просто ложно, а
# агент строит на нём команды. Ловим сами утверждения, а не упоминания ОС:
# «на Windows нужен Developer Mode» — законная оговорка, «ты на Windows» — нет.
PORTABILITY_RES = [
    (re.compile(r"(?:машина|среда|окружение)\s+пользовател[яю]", re.I),
     "утверждение о среде пользователя"),
    (re.compile(r"(?:^|[.;—-]\s*)(?:среда|окружение)\s*[—:-]\s*(?:Windows|Linux|macOS)", re.I),
     "среда объявлена как факт"),
    (re.compile(r"\bты на (?:Windows|Linux|macOS)\b", re.I),
     "обращение к пользователю как к носителю конкретной ОС"),
    (re.compile(r"\(у тебя\s*[—-]\s*да\)", re.I),
     "утверждение о конфигурации конкретного пользователя"),
    (re.compile(r"\bна Windows (?:используй|запускай|гоняй)\b", re.I),
     "предписание команд под конкретную ОС"),
    (re.compile(r"\bWindows-dev\b", re.I),
     "профиль машины разработчика зашит в инструкцию"),
    (re.compile(r"\b(?:соло|solo)-разработчик", re.I),
     "размер команды подан как данность"),
]
# Навыки, которым платформа посвящена по теме: там конкретика и есть предмет.
# Сейчас таких нет — `vps-ops` описывает Linux-сервер как объект работы, а не
# машину читателя, и под паттерны ниже не попадает.
PORTABILITY_EXEMPT: set[str] = set()


# --- модель находок --------------------------------------------------------

class Report:
    """Три уровня: ERROR и WARN образуют гейт, INFO — бэклог качества.

    INFO собирает то, что улучшать стоит, но что не должно валить сборку и
    заглушать реальные регрессии (крупные тела, отсутствие `verified`).
    """

    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []
        self.warns: list[tuple[str, str]] = []
        self.infos: list[tuple[str, str]] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append((where, msg))

    def warn(self, where: str, msg: str) -> None:
        self.warns.append((where, msg))

    def info(self, where: str, msg: str) -> None:
        self.infos.append((where, msg))


# --- разбор фронтматтера ---------------------------------------------------

def parse_frontmatter(text: str):
    """Строгий разбор YAML-фронтматтера в тех формах, которые разрешает контракт.

    Поддерживает: скаляр в строке (с кавычками и без), свёрнутый блок `>` / `|`
    и вложенный блок из пар `ключ: значение`. Всё остальное — ошибка, а не
    молчаливое игнорирование: валидатор заодно фиксирует допустимые формы.

    Возвращает (data, body, errors).
    """
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["файл не начинается с фронтматтера `---`"]
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text, ["фронтматтер не закрыт строкой `---`"]

    raw = text[4:end + 1]
    body = text[end + 5:]
    lines = raw.split("\n")
    data: dict[str, object] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if not m:
            errors.append(f"строка {i + 1} фронтматтера не разбирается: {line.strip()!r}")
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        i += 1
        if rest in (">", ">-", "|", "|-"):
            block: list[str] = []
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                block.append(lines[i].strip())
                i += 1
            joiner = " " if rest.startswith(">") else "\n"
            data[key] = joiner.join(x for x in block if x)
        elif rest == "":
            nested: dict[str, str] = {}
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                sub = lines[i].strip()
                i += 1
                if not sub:
                    continue
                sm = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", sub)
                if sm:
                    nested[sm.group(1)] = sm.group(2).strip().strip("\"'")
                else:
                    errors.append(f"вложенная строка не разбирается: {sub!r}")
            data[key] = nested
        else:
            data[key] = rest.strip().strip("\"'")
    return data, body, errors


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def discover_skills(repo: str) -> list[str]:
    root = os.path.join(repo, "skills")
    if not os.path.isdir(root):
        return []
    return sorted(
        d for d in os.listdir(root)
        if os.path.isfile(os.path.join(root, d, "SKILL.md"))
    )


# --- проверки навыка -------------------------------------------------------

def check_skill(repo: str, skill: str, rep: Report) -> dict:
    skill_dir = os.path.join(repo, "skills", skill)
    text = read(os.path.join(skill_dir, "SKILL.md"))
    fm, body, fm_errors = parse_frontmatter(text)
    for err in fm_errors:
        rep.error(skill, err)

    keys = set(fm)
    for unknown in sorted(keys - FM_TOP_KEYS):
        rep.error(skill, f"неизвестный ключ фронтматтера `{unknown}` "
                         f"(разрешены: {', '.join(sorted(FM_TOP_KEYS))})")
    for missing in sorted(FM_REQUIRED - keys):
        rep.error(skill, f"нет обязательного ключа `{missing}`")

    name = fm.get("name", "")
    if name != skill:
        rep.error(skill, f"`name: {name}` не совпадает с именем папки")
    if name and not NAME_RE.match(str(name)):
        rep.error(skill, f"`name` не в kebab-case: {name!r}")
    if len(str(name)) > NAME_MAX:
        rep.error(skill, f"`name` длиннее {NAME_MAX} символов")

    # Свёрнутый блок `>` склеивает строки через пробел: строка, оборванная на
    # дефисе, превращает `vps-ops` в `vps- ops` — имя навыка молча ломается.
    folded = re.search(r"^description: >\n((?:[ \t]+.*\n)+)", text, re.M)
    if folded and re.search(r"-[ \t]*\n", folded.group(1)):
        rep.error(skill, "строка описания оборвана на дефисе — в свёрнутом блоке "
                         "это разорвёт слово пробелом")

    desc = str(fm.get("description", ""))
    if not desc:
        rep.error(skill, "пустое описание")
    elif len(desc) > DESC_MAX:
        rep.error(skill, f"описание {len(desc)} символов — лимит {DESC_MAX}")
    elif len(desc) > DESC_WARN:
        rep.warn(skill, f"описание {len(desc)} символов — близко к лимиту {DESC_MAX}")
    if desc and not any(t in desc.lower() for t in TRIGGER_MARKERS):
        rep.warn(skill, "в описании нет условий срабатывания («Используй когда …»)")

    meta = fm.get("metadata")
    if meta is None:
        rep.warn(skill, "нет блока `metadata` с версией навыка")
    elif not isinstance(meta, dict):
        rep.error(skill, "`metadata` должен быть блоком `ключ: значение`")
    else:
        for unknown in sorted(set(meta) - FM_METADATA_KEYS):
            rep.error(skill, f"неизвестный ключ metadata.{unknown} "
                             f"(разрешены: {', '.join(sorted(FM_METADATA_KEYS))})")
        version = meta.get("version", "")
        if not version:
            rep.warn(skill, "нет `metadata.version`")
        elif not SEMVER_RE.match(version):
            rep.error(skill, f"`metadata.version: {version}` не semver (X.Y.Z)")
        verified = meta.get("verified")
        if verified:
            try:
                when = datetime.strptime(verified, "%Y-%m-%d").date()
            except ValueError:
                rep.error(skill, f"`metadata.verified: {verified}` — нужен формат YYYY-MM-DD")
            else:
                age = (date.today() - when).days
                if age > VERIFIED_STALE_DAYS:
                    rep.warn(skill, f"`verified` устарел на {age} дн. — перепроверь содержание")
        elif skill in VERSION_FRAGILE:
            rep.info(skill, "версионно-хрупкий навык без `metadata.verified`")

    body_lines = body.count("\n")
    body_bytes = len(body.encode("utf-8"))
    has_refs = os.path.isdir(os.path.join(skill_dir, "references"))
    if body_lines > BODY_WARN_LINES or body_bytes > BODY_WARN_BYTES:
        hint = "вынеси часть в references/" if not has_refs else "часть тела ещё выносима в references/"
        rep.info(skill, f"тело {body_lines} строк / {body_bytes / 1024:.1f} КБ — {hint}")

    # Посторонние .md в корне навыка: конвенция — только SKILL.md и references/.
    for entry in sorted(os.listdir(skill_dir)):
        if entry.endswith(".md") and entry != "SKILL.md":
            rep.error(skill, f"`{entry}` в корне навыка — переложи в `references/`")

    check_references(repo, skill, rep)

    return {
        "skill": skill, "desc_len": len(desc),
        "version": (meta or {}).get("version", "-") if isinstance(meta, dict) else "-",
        "lines": body_lines, "kb": body_bytes / 1024, "refs": has_refs,
    }


def check_references(repo: str, skill: str, rep: Report) -> None:
    skill_dir = os.path.join(repo, "skills", skill)
    mentioned: set[str] = set()
    for dirpath, _, files in os.walk(skill_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            src = os.path.join(dirpath, fname)
            for match in REF_PATH_RE.finditer(read(src)):
                rel = match.group(1)[2:] if match.group(1).startswith("./") else match.group(1)
                mentioned.add(rel)
                if not os.path.isfile(os.path.join(skill_dir, rel)):
                    rep.error(skill, f"{os.path.relpath(src, skill_dir)} ссылается на "
                                     f"отсутствующий `{rel}`")

    refs_dir = os.path.join(skill_dir, "references")
    if not os.path.isdir(refs_dir):
        return
    for dirpath, _, files in os.walk(refs_dir):
        for fname in files:
            rel = os.path.relpath(os.path.join(dirpath, fname), skill_dir).replace(os.sep, "/")
            if rel not in mentioned:
                rep.warn(skill, f"`{rel}` не упомянут ни в одном файле навыка (осиротевший)")


# --- проверки уровня репозитория -------------------------------------------

def check_privacy(repo: str, rep: Report) -> None:
    """Ищет личные данные в публикуемых файлах: домашние пути с логином."""
    for dirpath, dirs, files in os.walk(repo):
        # .claude/.opencode — локальное состояние, оно в .gitignore и не публикуется.
        dirs[:] = [d for d in dirs if d not in (".git", ".claude", ".opencode",
                                                "__pycache__", ".venv")]
        for fname in files:
            if not fname.endswith((".md", ".jsonl", ".json", ".py", ".yml")):
                continue
            path = os.path.join(dirpath, fname)
            rel = os.path.relpath(path, repo).replace(os.sep, "/")
            for i, line in enumerate(read(path).splitlines(), 1):
                for m in HOME_PATH_RE.finditer(line):
                    if m.group(1).lower() in HOME_PLACEHOLDERS:
                        continue
                    rep.error(rel, f"строка {i}: домашний путь с логином "
                                   f"`{m.group(0)}` — обезличь перед публикацией")


def check_portability(repo: str, skills: list[str], rep: Report) -> None:
    """Ищет привязку инструкций к ОС, оболочке и размеру команды пользователя."""
    targets = [f"skills/{s}/SKILL.md" for s in skills if s not in PORTABILITY_EXEMPT]
    for skill in skills:
        if skill in PORTABILITY_EXEMPT:
            continue
        refs = os.path.join(repo, "skills", skill, "references")
        if os.path.isdir(refs):
            targets += [f"skills/{skill}/references/{f}" for f in sorted(os.listdir(refs))
                        if f.endswith(".md")]
    targets += ["README.md"]

    for rel in targets:
        path = os.path.join(repo, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            continue
        for i, line in enumerate(read(path).splitlines(), 1):
            for pattern, why in PORTABILITY_RES:
                if pattern.search(line):
                    rep.warn(rel, f"строка {i}: {why} — библиотеку ставят "
                                  f"на другой ОС, переформулируй нейтрально")
                    break


def check_readme(repo: str, skills: list[str], rep: Report) -> None:
    readme = read(os.path.join(repo, "README.md"))

    catalogue = set(re.findall(r"\[`([\w\-]+)`\]\(skills/\1/\)", readme))
    tree: set[str] = set()
    in_skills = False
    for line in readme.splitlines():
        if re.match(r"^(?:├|└)── skills/$", line):
            in_skills = True
            continue
        if in_skills:
            m = re.match(r"^│\s+(?:├|└)── ([\w\-]+)/$", line)
            if m:
                tree.add(m.group(1))
            else:
                in_skills = False
    for skill in skills:
        if skill not in catalogue:
            rep.error("README.md", f"навык `{skill}` отсутствует в каталоге")
        if skill not in tree:
            rep.error("README.md", f"навык `{skill}` отсутствует в дереве репозитория")
    for extra in sorted(catalogue - set(skills)):
        rep.error("README.md", f"в каталоге есть `{extra}`, которого нет в репозитории")

    badge = re.search(r"skills-(\d+)-", readme)
    if not badge:
        rep.warn("README.md", "не найден бейдж «Skills: N»")
    elif int(badge.group(1)) != len(skills):
        rep.error("README.md", f"бейдж обещает {badge.group(1)} навыков, фактически {len(skills)}")


def check_manifests(repo: str, skills: list[str], rep: Report) -> None:
    plugin_path = os.path.join(repo, ".claude-plugin", "plugin.json")
    market_path = os.path.join(repo, ".claude-plugin", "marketplace.json")
    try:
        plugin = json.loads(read(plugin_path))
        market = json.loads(read(market_path))
    except (OSError, json.JSONDecodeError) as exc:
        rep.error(".claude-plugin", f"манифест не читается: {exc}")
        return

    entries = [p for p in market.get("plugins", []) if p.get("name") == plugin.get("name")]
    if not entries:
        rep.error("marketplace.json", f"нет записи для плагина `{plugin.get('name')}`")
        return
    entry = entries[0]
    if entry.get("version") != plugin.get("version"):
        rep.error(".claude-plugin", f"версии разошлись: plugin.json {plugin.get('version')} "
                                    f"vs marketplace.json {entry.get('version')}")
    if not SEMVER_RE.match(str(plugin.get("version", ""))):
        rep.error("plugin.json", f"версия `{plugin.get('version')}` не semver")

    # Описания манифестов называют число навыков — оно протухает при каждом
    # пополнении библиотеки.
    for label, path in (("plugin.json", plugin_path), ("marketplace.json", market_path)):
        claimed = re.search(r"(\d+)\s+Agent Skills", read(path))
        if claimed and int(claimed.group(1)) != len(skills):
            rep.error(label, f"описание обещает {claimed.group(1)} навыков, "
                             f"фактически {len(skills)}")


# --- бамп версий -----------------------------------------------------------

def git(repo: str, *args: str) -> tuple[int, str]:
    # encoding задаётся явно: под Windows text=True декодирует выводом локали
    # (cp1251) и падает на кириллице в содержимом навыков.
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "").strip()


def rev(repo: str, ref: str) -> str | None:
    if not ref or set(ref) <= {"0"}:  # пустой ref или нули из github.event.before
        return None
    code, out = git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    return out if code == 0 and out else None


def resolve_base(repo: str, requested: str | None) -> tuple[str | None, str | None]:
    """Возвращает (sha, примечание).

    Явно переданная база, которая не резолвится, — не повод молча сравнить с
    чем-то другим: подмена дала бы ложно-зелёный результат в CI. Про подмену и
    про пропуск проверки всегда сообщаем вслух.
    """
    # Пустая база и строка из нулей (github.event.before на новой ветке)
    # считаются «база не задана», всё остальное — явно запрошенная.
    if requested and set(requested) != {"0"}:
        found = rev(repo, requested)
        if found:
            return found, None
        note = f"база `{requested}` не найдена"
    else:
        note = None

    for fallback in ("origin/master", "origin/main", "HEAD~1"):
        found = rev(repo, fallback)
        if found:
            return found, (f"{note} — сравниваю с `{fallback}`" if note else None)
    return None, (f"{note}; запасная база тоже недоступна" if note
                  else "база для сравнения не найдена")


def version_at(repo: str, ref: str, path: str) -> str | None:
    code, out = git(repo, "show", f"{ref}:{path}")
    if code != 0:
        return None
    if path.endswith(".json"):
        try:
            return json.loads(out).get("version")
        except json.JSONDecodeError:
            return None
    fm, _, _ = parse_frontmatter(out if out.endswith("\n") else out + "\n")
    meta = fm.get("metadata")
    return meta.get("version") if isinstance(meta, dict) else None


def check_bump(repo: str, skills: list[str], base: str | None, rep: Report) -> None:
    resolved, note = resolve_base(repo, base)
    if note:
        rep.warn("git", f"{note}")
    if not resolved:
        rep.warn("git", "проверка бампа версий пропущена")
        return
    code, out = git(repo, "diff", "--name-only", resolved, "HEAD")
    if code != 0:
        rep.warn("git", "не удалось получить дифф — проверка бампа версий пропущена")
        return

    changed = [p for p in out.splitlines() if p]
    touched = {p.split("/")[1] for p in changed
               if p.startswith("skills/") and p.count("/") >= 2} & set(skills)
    if not touched:
        return

    plugin_rel = ".claude-plugin/plugin.json"
    was = version_at(repo, resolved, plugin_rel)
    now = json.loads(read(os.path.join(repo, plugin_rel))).get("version")
    if was is not None and was == now:
        rep.error("plugin.json", f"изменены навыки ({', '.join(sorted(touched))}), "
                                 f"а версия плагина осталась {now} — кэш маркетплейса "
                                 f"не увидит обновление")

    for skill in sorted(touched):
        rel = f"skills/{skill}/SKILL.md"
        if rel not in changed:
            continue  # менялись только references — бамп на усмотрение автора
        before = version_at(repo, resolved, rel)
        if before is None:
            continue  # новый навык
        fm, _, _ = parse_frontmatter(read(os.path.join(repo, "skills", skill, "SKILL.md")))
        meta = fm.get("metadata")
        after = meta.get("version") if isinstance(meta, dict) else None
        if before == after:
            rep.error(skill, f"SKILL.md изменён, а `metadata.version` остался {after}")


# --- вывод -----------------------------------------------------------------

def print_table(stats: list[dict]) -> None:
    print(f"{'навык':28} {'desc':>5} {'верс':>7} {'строк':>6} {'КБ':>6}  refs")
    print("-" * 64)
    for row in sorted(stats, key=lambda r: -r["desc_len"]):
        print(f"{row['skill']:28} {row['desc_len']:5} {row['version']:>7} "
              f"{row['lines']:6} {row['kb']:6.1f}  {'да' if row['refs'] else '—'}")
    total = sum(r["desc_len"] for r in stats)
    print("-" * 64)
    print(f"описаний суммарно: {total} символов "
          f"(~{int(total / 1.8)} токенов в каждой сессии)")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Валидация библиотеки навыков llm-skills")
    parser.add_argument("--strict", action="store_true", help="считать предупреждения ошибками")
    parser.add_argument("--check-bump", action="store_true", help="проверить бамп версий против базы")
    parser.add_argument("--base", help="git-ref базы для --check-bump (по умолчанию origin/master)")
    parser.add_argument("--list", action="store_true", help="вывести таблицу метрик по навыкам")
    parser.add_argument("--info", action="store_true", help="показать бэклог качества (INFO)")
    args = parser.parse_args()

    skills = discover_skills(REPO)
    if not skills:
        print("не найдено ни одного навыка в skills/ — запусти из корня репозитория", file=sys.stderr)
        return 1

    rep = Report()
    stats = [check_skill(REPO, skill, rep) for skill in skills]
    check_readme(REPO, skills, rep)
    check_manifests(REPO, skills, rep)
    check_privacy(REPO, rep)
    check_portability(REPO, skills, rep)
    if args.check_bump:
        check_bump(REPO, skills, args.base, rep)

    if args.list:
        print_table(stats)

    for where, msg in rep.errors:
        print(f"ERROR  {where:28} {msg}")
    for where, msg in rep.warns:
        print(f"WARN   {where:28} {msg}")
    if args.info or args.list:
        for where, msg in rep.infos:
            print(f"INFO   {where:28} {msg}")
    if rep.errors or rep.warns or ((args.info or args.list) and rep.infos):
        print()

    summary = (f"навыков: {len(skills)} | ошибок: {len(rep.errors)} | "
               f"предупреждений: {len(rep.warns)} | заметок: {len(rep.infos)}")
    if rep.infos and not (args.info or args.list):
        summary += " (показать: --info)"
    print(summary)

    if rep.errors:
        return 1
    if rep.warns and args.strict:
        print("--strict: предупреждения считаются ошибками")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
