# Kleinanzeigen Matrix Bot

A Matrix bot that monitors new listings on [kleinanzeigen.de](https://kleinanzeigen.de) and sends notifications to Matrix rooms.

[Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md)

## Features

- Monitors Kleinanzeigen searches by URL
- Periodic checks with configurable interval
- Sends new listing notifications to Matrix rooms
- Multi-room support: each room has its own set of searches
- Built on [matrix-nio](https://github.com/poljar/matrix-nio)

## Quick Start

### 1. Create a Matrix account for the bot

Register a separate user on any homeserver (matrix.org, self-hosted, etc.).

### 2. Clone and configure

```bash
git clone <repo-url> && cd matrix-kleinanzeigen-bot
cp .env.example .env
```

Edit `.env` with your bot's credentials.

### 3. Run

**Docker:**
```bash
docker compose up -d
```

**Local:**
```bash
pip install -r requirements.txt
python main.py
```

### 4. Invite the bot to a room

Invite `@your-bot:matrix.org` to any Matrix room. The bot accepts invites automatically.

## Commands

| Command | Description |
|---|---|
| `!add <url> [name]` | Add a search. URL is a Kleinanzeigen search results page |
| `!remove <id>` | Remove a search by ID |
| `!list` | Show all searches in this room |
| `!check` | Force an immediate check |
| `!help` | Show help |

## Example

```
!add https://www.kleinanzeigen.de/s-bicycles/berlin/k0c217 Bicycles Berlin
✅ Added search #1: Bicycles Berlin

-- 10 minutes later --

**New listings for «Bicycles Berlin»**

• [Trek Domane AL 2 2023](https://...) — *750 €*
  _Berlin, Mitte_
• [Canyon Endurace CF SL](https://...) — *1,200 €*
  _Berlin, Prenzlauer Berg_
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MATRIX_HOMESERVER` | `https://matrix.org` | Bot's homeserver |
| `MATRIX_USER` | — | Full MXID login |
| `MATRIX_PASSWORD` | — | Password |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/kleinanzeigen.db` | Database path |
| `CHECK_INTERVAL` | `600` | Check interval in seconds |

## Disclaimer

Automated access to kleinanzeigen.de may violate their Terms of Service (Section 5 of the [Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/)). The developers assume no liability for any damages or legal consequences. Use at your own risk.

## License

MIT
