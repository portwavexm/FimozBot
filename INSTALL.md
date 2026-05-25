# FimozBot Installation Guide

## Три способа установки

### 1. Автоматическая установка (Рекомендуется) ⭐

Самый простой способ - просто запустите установщик:

**Вариант A: Через BAT файл**
```
install.bat
```

**Вариант B: Через PowerShell**
```
powershell -ExecutionPolicy Bypass -File install.ps1
```

Установщик автоматически:
- ✅ Проверит Python и Java
- ✅ Установит недостающие компоненты (если нужно)
- ✅ Создаст виртуальное окружение
- ✅ Установит все зависимости
- ✅ Настроит конфигурацию
- ✅ Создаст ярлыки на рабочем столе

### 2. Ручная установка

Если автоматическая установка не сработала:

#### Шаг 1: Установить зависимости

**Python 3.10+**
- Скачайте с https://www.python.org/downloads/
- При установке отметьте "Add Python to PATH"

**Java 11+**
- Скачайте с https://www.java.com/en/download/
- Java требуется для Lavalink

**Git**
- Скачайте с https://git-scm.com/download/win

#### Шаг 2: Клонирование/Извлечение

Если скачали ZIP архив:
```
Распакуйте в C:\FimozBot
```

Если через git:
```
git clone https://github.com/portwavexm/FimozBot.git C:\FimozBot
cd C:\FimozBot
```

#### Шаг 3: Создание виртуального окружения

```
python -m venv .venv
.venv\Scripts\activate
```

#### Шаг 4: Установка зависимостей

```
pip install -r requirements.txt
```

#### Шаг 5: Конфигурация

Отредактируйте файл `.env`:

```env
DISCORD_TOKEN=YOUR_DISCORD_TOKEN_HERE
LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=2333
LAVALINK_PASSWORD=YOUR_LAVALINK_PASSWORD_HERE
SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID_HERE
SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET_HERE
```

**Где получить токены:**
- **Discord Token**: https://discord.com/developers/applications
  1. Create Application
  2. Go to "Bot" tab
  3. Click "Add Bot"
  4. Copy the token
  
- **Spotify Credentials**: https://developer.spotify.com/dashboard
  1. Create Application
  2. Copy Client ID and Client Secret

#### Шаг 6: Запуск

**Запустить Lavalink:**
```
cd lavalink-server
java -jar Lavalink.jar
```

**В новом терминале запустить бота:**
```
.venv\Scripts\activate
python main.py
```

### 3. Docker установка

Если у вас установлен Docker:

```bash
docker-compose up -d
```

## Требования

- **ОС**: Windows 7+
- **Python**: 3.10 или выше
- **Java**: 11 или выше (для Lavalink)
- **Git**: для клонирования репозитория
- **RAM**: минимум 512MB (рекомендуется 1GB+)
- **Интернет**: для загрузки зависимостей

## Решение проблем

### "Python not found"
- Установите Python с https://www.python.org/downloads/
- При установке отметьте опцию "Add Python to PATH"
- Перезагрузитесь после установки

### "Git not found"
- Установите Git с https://git-scm.com/download/win

### "Java not found"
- Установите Java с https://www.java.com/en/download/
- Требуется для работы Lavalink (музыкальный сервер)

### Бот не подключается к Discord
- Проверьте DISCORD_TOKEN в `.env`
- Убедитесь что токен не содержит кавычек

### "No module named 'discord'"
- Активируйте виртуальное окружение: `.venv\Scripts\activate`
- Переустановите зависимости: `pip install -r requirements.txt`

### Lavalink не запускается
- Проверьте что Java установлена: `java -version`
- Убедитесь что порт 2333 не занят

## После установки

1. **Добавьте бота на свой Discord сервер:**
   - Перейдите в https://discord.com/developers/applications
   - Выберите ваше приложение
   - Перейдите в "OAuth2" → "URL Generator"
   - Выберите scopes: `bot`
   - Выберите permissions: `Send Messages`, `Connect`, `Speak`
   - Скопируйте сгенерированный URL и откройте его

2. **Запустите бота:**
   - Откройте терминал в папке FimozBot
   - Активируйте venv: `.venv\Scripts\activate`
   - Запустите: `python main.py`

3. **Используйте команды:**
   - `/play песня` - Воспроизвести
   - `/pause` - Пауза
   - `/skip` - Пропустить
   - `/queue` - Очередь

## Получение помощи

- 📖 Читайте README.md для полной документации
- 🐛 Создавайте issues: https://github.com/portwavexm/FimozBot/issues
- 💬 Discord: [ссылка на сервер]

## Обновление

Для обновления бота до последней версии:

```
cd C:\FimozBot
git pull origin main
pip install -r requirements.txt
```
