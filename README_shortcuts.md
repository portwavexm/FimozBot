Создание ярлыков для быстрого запуска

Файлы в репозитории:
- `start_bot.bat` — двойной клик запускает `run.py` (Lavalink + бот) через cmd.
- `start_bot.ps1` — PowerShell‑скрипт с доп. опциями: виртуальное окружение, логи, авто‑перезапуск.
- `create_shortcuts.ps1` — создаёт два ярлыка на рабочем столе:
  - "Start FimozBot (bat)" — запускает `start_bot.bat`
  - "Start FimozBot (PowerShell)" — запускает `start_bot.ps1` через `powershell.exe -ExecutionPolicy Bypass`

Как создать ярлыки (PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File .\create_shortcuts.ps1
```

Запуск как администратор:
- Если нужно запускать с повышенными правами (например, для установки службы), щёлкни правой кнопкой по ярлыку и выбери "Запуск от имени администратора".
- Для постоянного запуска с правами администратора можно создать задачу в Планировщике (Task Scheduler) с включённым "Run with highest privileges".

Примечания:
- Политика выполнения PowerShell может блокировать скрипты. В таком случае используй `-ExecutionPolicy Bypass` при запуске.
- Плейлисты сохраняются в `config/playlists.json` (или в пути, заданном аргументом `-PlaylistStore`).
