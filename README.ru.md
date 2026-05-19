# Kleinanzeigen Matrix Bot

Бот для Matrix, который отслеживает новые объявления на [kleinanzeigen.de](https://kleinanzeigen.de) и уведомляет в Matrix-комнаты.

## Возможности

- Поиск по URL-ссылкам Kleinanzeigen
- Периодическая проверка (настраиваемый интервал)
- Уведомления о новых объявлениях в Matrix-комнату
- Поддержка нескольких комнат, в каждой свой набор поисков
- Работает через [matrix-nio](https://github.com/poljar/matrix-nio)

## Быстрый старт

### 1. Создать Matrix-аккаунт для бота

Зарегистрируй отдельного пользователя на любом homeserver (matrix.org, eigene, etc.).

### 2. Клонировать и настроить

```bash
git clone <repo-url> && cd matrix-kleinanzeigen-bot
cp .env.example .env
```

Отредактируй `.env` — укажи логин/пароль бота.

### 3. Запустить

**Через Docker:**
```bash
docker compose up -d
```

**Локально:**
```bash
pip install -r requirements.txt
python main.py
```

### 4. Пригласить бота в комнату

Пригласи `@your-bot:matrix.org` в Matrix-комнату. Бот принимает приглашения автоматически.

## Команды

| Команда | Описание |
|---|---|
| `!add <url> [название]` | Добавить поиск. URL — ссылка на страницу результатов Kleinanzeigen |
| `!remove <id>` | Удалить поиск по ID |
| `!list` | Показать все поиски в этой комнате |
| `!check` | Принудительная проверка прямо сейчас |
| `!help` | Показать справку |

## Пример

```
!add https://www.kleinanzeigen.de/s-grafikkarten/berlin/k0c225 Велосипеды Берлин
✅ Добавлен поиск #1: Велосипеды Берлин

-- через 10 минут --

**Новые объявления по поиску «Велосипеды Берлин»**

• [Trek Domane AL 2 2023](https://...) — *750 €*
  _Berlin, Mitte_
• [Canyon Endurace CF SL](https://...) — *1.200 € VB*
  _Berlin, Prenzlauer Berg_
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `MATRIX_HOMESERVER` | `https://matrix.org` | Homeserver бота |
| `MATRIX_USER` | — | Логин (полный MXID) |
| `MATRIX_PASSWORD` | — | Пароль |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/kleinanzeigen.db` | Путь к БД |
| `CHECK_INTERVAL` | `600` | Интервал проверки в секундах |

## Лицензия

MIT
