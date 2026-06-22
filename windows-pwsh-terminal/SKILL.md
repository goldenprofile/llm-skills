---
name: windows-pwsh-terminal
description: Методика диагностики и модернизации терминала на Windows — WezTerm + PowerShell 7 (pwsh) + scoop. Чеклист текущего состояния, развилки для согласования с пользователем и типовые грабли (а не снимок чужого конфига). Используй когда пользователь просит настроить/улучшить терминал, pwsh-профиль или WezTerm, чинит историю команд/автодополнения/промпт, переносит сетап на новую машину, или упоминает «настроить терминал», «pwsh профиль», «wezterm», «starship», «atuin», «fzf», «scoop», «dotfiles».
metadata:
  version: 1.0.0
---

# Windows pwsh + WezTerm — тюнинг терминала

Методика, **НЕ дамп конфига**. Цель — модернизировать терминал, согласуя развилки с пользователем и не наступая на типовые грабли. Все user-facing ответы — на русском.

## Workflow

1. **Диагностика** — собери текущее состояние (чеклист ниже). Запусти `scripts/diagnose.ps1` (read-only, ничего не меняет).
2. **Предложи** тирами по ROI: сначала «уже стоит, но не подключено», потом доустановки.
3. **Согласуй развилки** через AskUserQuestion. Не решай за пользователя keybindings и pager-стратегию.
4. **Применяй** точечно, с комментариями в профиле и `.wezterm.lua`. Готовые команды/сниппеты — в [REFERENCE.md](REFERENCE.md).
5. **Проверь** — загрузи профиль в свежем pwsh, убедись что биндинги/функции на месте и нет ошибок (см. «Проверка»).

## Чеклист диагностики

- `$PROFILE.CurrentUserCurrentHost` (путь + существование), `$PSVersionTable.PSVersion`.
- Тулзы на PATH: starship, atuin, fzf/fd/rg, zoxide, eza, bat, delta, lazygit, yazi, gh, carapace, btm/dust/duf/procs, glow, tldr.
- Модули: PSReadLine (версия, EditMode, PredictionSource), PSFzf, PSCompletions.
- Что уже инициализировано в профиле: starship, zoxide, atuin, fzf, carapace, OSC 7.
- История PSReadLine: `HistorySavePath` + файл существует? (история не теряется даже без atuin).

## Развилки (согласовать с пользователем)

- **atuin**: только `Ctrl+R` (`--disable-up-arrow`, стрелка ↑ остаётся за PSReadLine) ИЛИ `Ctrl+R` + ↑.
- **WezTerm leader**: НЕ `Ctrl+A` при Emacs-режиме PSReadLine. Дефолт — `Ctrl+Space`.
- **Pager**: delta для git; bat — только тема (`BAT_THEME`), не глобальный `$PAGER` (см. грабли).
- **Доустановки (опционально)**: btm, dust, duf, procs, glow, tldr, carapace.

## Грабли (проверять ВСЕГДА)

- **atuin поддерживает Windows** (18.16+) — старые TODO «только Linux» неверны.
- **`Ctrl+A` в Emacs-режиме** = «в начало строки» → не вешать на WezTerm leader.
- **`bat` как `$env:PAGER`** = рекурсия, если `cat` — алиас на bat. Не ставить глобально; на Windows нет `man`.
- **`md`** = встроенный mkdir в pwsh → не делать алиасом.
- **carapace + PSCompletions** могут спорить за команду → carapace-init должен легко комментироваться.
- Глифы Nerd Font в `.wezterm.lua` — только через `utf8.char(0x...)`.

## Проверка

Грузи профиль в свежем pwsh и проверяй биндинги/функции (`Get-PSReadLineKeyHandler`, `Get-Command`). **Игнорируй** ошибки про `PredictionSource`/«Неверный дескриптор» — это артефакт неинтерактивного запуска с перенаправленным выводом, в реальной сессии их нет. Конфиг WezTerm валидируй: `wezterm --config-file <path> show-keys`.

Подробные команды и сниппеты — [REFERENCE.md](REFERENCE.md).
