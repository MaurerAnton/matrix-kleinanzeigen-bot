# Kleinanzeigen / Leboncoin Matrix Bot

A Matrix bot that monitors new listings on [kleinanzeigen.de](https://kleinanzeigen.de) and [leboncoin.fr](https://leboncoin.fr), sending notifications to Matrix rooms.

[Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md)

## Features

- Monitors Kleinanzeigen and Leboncoin searches by URL
- Periodic checks with configurable interval
- Sends new listing notifications to Matrix rooms
- Multi-room support: each room has its own set of searches
- Built on [matrix-nio](https://github.com/poljar/matrix-nio)
- Optional E2EE support (requires `python-olm`)

## Supported Sites

| Site | Status | Notes |
|---|---|---|
| kleinanzeigen.de | Working | HTML scraping via aiohttp + BeautifulSoup |
| leboncoin.fr | Experimental | SPA with DataDome protection; requires headless browser or API token |

## Quick Start

### 1. Create a Matrix account for the bot

Register a separate user on any homeserver (matrix.org, self-hosted, etc.).

### 2. Clone and configure

```bash
git clone https://github.com/MaurerAnton/matrix-kleinanzeigen-bot
cd matrix-kleinanzeigen-bot
cp .env.example .env
```

Edit `.env` with your bot's credentials. Use either password or access token.

### 3. Run

**Docker:**
```bash
docker compose up -d
```

**Local:**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 4. Invite the bot to a room

Invite `@your-bot:matrix.org` to any Matrix room. The bot accepts invites automatically.

## Commands

| Command | Description |
|---|---|
| `!add <url> [name]` | Add a search. Works with kleinanzeigen.de and leboncoin.fr URLs |
| `!remove <id>` | Remove a search by ID |
| `!list` | Show all searches in this room |
| `!check` | Force an immediate check |
| `!disclaimer` | Show legal disclaimer |
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
| `MATRIX_ACCESS_TOKEN` | — | Access token (alternative to password) |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/kleinanzeigen.db` | Database path |
| `CHECK_INTERVAL` | `600` | Check interval in seconds |

## E2EE

The bot supports encrypted rooms when `python-olm` is available:

```bash
# Arch
sudo pacman -S libolm make
# Debian/Ubuntu
sudo apt install libolm-dev make
# Then in venv:
pip install python-olm
```

E2EE activates automatically on next restart.

## Disclaimer

Automated access to kleinanzeigen.de and leboncoin.fr may violate their Terms of Service. The developers assume no liability for any damages or legal consequences. Use at your own risk.

## License

MIT
