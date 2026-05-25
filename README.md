# FimozBot - Discord Music Bot

Полнофункциональный музыкальный бот для Discord с поддержкой YouTube, Spotify и других сервисов.

## Требования

- Python 3.10+
- Java 11+ (для Lavalink сервера)
- Git

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/portwavexm/FimozBot.git
cd FimozBot
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации

Отредактируйте файл `.env`:

```env
# Discord Bot Token (Required)
DISCORD_TOKEN=YOUR_DISCORD_TOKEN_HERE

# Lavalink Configuration (Required)
LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=2333
LAVALINK_PASSWORD=YOUR_LAVALINK_PASSWORD_HERE

# Spotify API Credentials (Required)
SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID_HERE
SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET_HERE
```

**Где получить токены:**
- **Discord Token**: https://discord.com/developers/applications (Create Application → Bot → Copy Token)
- **Spotify Credentials**: https://developer.spotify.com/dashboard (Create App)

### 5. Запуск Lavalink сервера

Lavalink требует отдельного запуска:

```bash
cd lavalink-server
java -jar Lavalink.jar
```

Lavalink будет доступен на `127.0.0.1:2333`

> **Примечание**: Убедитесь что файл `application.yml` в `lavalink-server/` содержит правильный пароль:
> ```yaml
> lavalink:
>   server:
>     password: "YOUR_LAVALINK_PASSWORD_HERE"
> ```

### 6. Запуск бота

В новом терминале (с активированным виртуальным окружением):

```bash
python main.py
```

или

```bash
python run.py
```

## Команды бота

- `/play <песня>` - Воспроизвести песню с YouTube или Spotify
- `/pause` - Пауза
- `/resume` - Возобновить
- `/skip` - Пропустить текущую песню
- `/stop` - Остановить и очистить очередь
- `/queue` - Показать очередь
- `/now` - Показать текущую песню

## Быстрый запуск (Windows)

Используйте готовые скрипты:

```bash
# Запуск бота
start_bot.bat

# или
start_bot.ps1
```

## Структура проекта

```
FimozBot/
├── cogs/                    # Discord команды и функции
│   └── music.py            # Музыкальные команды
├── config/                 # Конфигурационные файлы
│   └── playlists.json      # Сохраненные плейлисты
├── lavalink-server/        # Lavalink сервер для музыки
│   ├── Lavalink.jar        # Основной jar файл
│   ├── application.yml     # Конфигурация Lavalink
│   └── plugins/            # Плагины (YouTube, Spotify и т.д.)
├── utils/                  # Утилиты
│   ├── spotify.py          # Интеграция Spotify
│   └── playlist_store.py   # Управление плейлистами
├── scripts/                # Дополнительные скрипты
├── tests/                  # Тесты
├── main.py                 # Главный файл бота
├── run.py                  # Альтернативный запуск
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения
└── Dockerfile              # Docker конфигурация
```

## Docker

Можно запустить бота в Docker:

```bash
docker-compose up -d
```

## Решение проблем

### Бот не соединяется с Lavalink

1. Проверьте что Lavalink запущен на `127.0.0.1:2333`
2. Убедитесь что пароль в `.env` совпадает с паролем в `lavalink-server/application.yml`
3. Проверьте логи: `tail -f logs/bot.log`

### "No module named 'discord'"

Убедитесь что виртуальное окружение активировано и зависимости установлены:

```bash
pip install -r requirements.txt
```

### Spotify токены не работают

Получите новые токены с https://developer.spotify.com/dashboard и обновите `.env`

## Логи

Логи сохраняются в папке `logs/`:

```bash
tail -f logs/bot.log
```

## Поддержка

- Discord сервер: [ссылка]
- Issues: https://github.com/portwavexm/FimozBot/issues

## Кредиты

- [discord.py](https://github.com/Rapptz/discord.py)
- [Lavalink](https://github.com/lavalink-devs/Lavalink)
- [wavelink](https://github.com/PythonTonie/Wavelink)
