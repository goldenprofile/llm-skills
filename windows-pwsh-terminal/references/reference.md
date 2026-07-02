# REFERENCE — команды и сниппеты

> Переносимые рецепты. Канон конкретного пользователя — в его dotfiles-репо/заметках.

## Рекомендуемый стек (scoop)

| Категория | Тул | Установка |
|---|---|---|
| Промпт | starship | `scoop install starship` |
| История | atuin | `scoop install atuin` |
| Fuzzy | fzf + fd + rg | `scoop install fzf fd ripgrep` |
| Навигация | zoxide | `scoop install zoxide` |
| ls / cat | eza, bat | `scoop install eza bat` |
| git | delta, lazygit | `scoop install delta lazygit` |
| Файлы | yazi | `scoop install yazi` |
| Мониторинг | btm, dust, duf, procs | `scoop install bottom dust duf procs` |
| Доки | glow, tldr | `scoop install glow tealdeer` |
| Автодополнения | carapace | `scoop install carapace-bin` |

Модули PowerShell: `Install-Module PSReadLine, PSFzf, PSCompletions -Scope CurrentUser`.

## Профиль pwsh — сниппеты

### atuin (история), только Ctrl+R
```powershell
if ($IsRealConsole -and (Get-Module PSReadLine)) {
    atuin init powershell --disable-up-arrow | Out-String | Invoke-Expression
}
```
Импорт существующей истории: `atuin import powershell`.

### fzf + PSFzf (Ctrl+T файлы, Alt+C cd)
```powershell
Import-Module PSFzf -ErrorAction SilentlyContinue
if ($IsRealConsole -and (Get-Module PSFzf)) {
    Set-PsFzfOption -PSReadlineChordProvider 'Ctrl+t' -PSReadlineChordSetLocation 'Alt+c'
}
$env:FZF_DEFAULT_COMMAND = 'fd --type f --hidden --exclude .git'
$env:FZF_DEFAULT_OPTS = '--height 60% --layout reverse --border --info inline ' +
    '--preview "bat --color=always --style=numbers --line-range=:500 {} 2>nul"'
```

### OSC 7 — директория для новых панелей (совместимо со starship)
```powershell
function Invoke-Starship-PreCommand {
    $loc = $executionContext.SessionState.Path.CurrentLocation
    if ($loc.Provider.Name -eq 'FileSystem') {
        $p = $loc.ProviderPath -replace '\\', '/'; $esc = [char]27
        $host.UI.Write("$esc]7;file://$env:COMPUTERNAME/$p$esc\")
    }
}
```

### carapace (после PSReadLine; нужен Tab = MenuComplete)
```powershell
if (Get-Command carapace -ErrorAction SilentlyContinue) {
    carapace _carapace powershell | Out-String | Invoke-Expression
}
```

### Удобства
```powershell
$env:EDITOR = 'zed --wait'; $env:VISUAL = $env:EDITOR
$env:BAT_THEME = 'Catppuccin Mocha'
function update { topgrade @args }
```

## git + delta (глобально)
```
git config --global core.pager delta
git config --global interactive.diffFilter "delta --color-only"
git config --global delta.navigate true
git config --global delta.line-numbers true
git config --global delta.syntax-theme "Catppuccin Mocha"
```

## WezTerm — leader + панели (.wezterm.lua)
```lua
local act = wezterm.action
config.leader = { key = 'Space', mods = 'CTRL', timeout_milliseconds = 1500 }
config.keys = {
  { key = '\\', mods = 'LEADER', action = act.SplitHorizontal { domain = 'CurrentPaneDomain' } },
  { key = '-',  mods = 'LEADER', action = act.SplitVertical   { domain = 'CurrentPaneDomain' } },
  { key = 'h', mods = 'LEADER', action = act.ActivatePaneDirection 'Left' },
  { key = 'j', mods = 'LEADER', action = act.ActivatePaneDirection 'Down' },
  { key = 'k', mods = 'LEADER', action = act.ActivatePaneDirection 'Up' },
  { key = 'l', mods = 'LEADER', action = act.ActivatePaneDirection 'Right' },
  { key = 'z', mods = 'LEADER', action = act.TogglePaneZoomState },
  { key = 'x', mods = 'LEADER', action = act.CloseCurrentPane { confirm = true } },
  { key = 'c', mods = 'LEADER', action = act.SpawnTab 'CurrentPaneDomain' },
}
```
Валидация: `wezterm --config-file "$env:USERPROFILE\.wezterm.lua" show-keys`.

## Грабли (подробно)

- **atuin на Windows**: 18.16+ официально поддерживает pwsh (`atuin init powershell`). Не верь старым «только Linux».
- **Ctrl+A**: в Emacs-режиме PSReadLine = beginning-of-line; leader на нём ломает редактирование строки → бери `Ctrl+Space`.
- **bat как $PAGER**: если `cat` → bat, bat вызывает себя пейджером → рекурсия. На Windows нет `man`. Используй delta (git) + `BAT_THEME` для единого вида.
- **md**: встроенный mkdir в pwsh — не переопределять алиасом.
- **carapace vs PSCompletions**: оба регистрируют ArgumentCompleter; при конфликте по команде закомментируй carapace-init (PSCompletions останется).
- **volta из scoop** может падать (`Install failed`), а рабочий ставится официальным инсталлятором в `C:\Program Files\Volta`. Проверяй `Get-Command volta` перед выводами.
- **Nerd Font глифы** в `.wezterm.lua` — только через `utf8.char(0x....)`, прямые символы не сохраняются.
