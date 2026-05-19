# Kleinanzeigen Matrix Bot

Ein Matrix-Bot, der neue Anzeigen auf [kleinanzeigen.de](https://kleinanzeigen.de) überwacht und Benachrichtigungen an Matrix-Räume sendet.

[English](README.md) | [Français](README.fr.md) | [Español](README.es.md)

## Funktionen

- Überwachung von Kleinanzeigen-Suchanfragen per URL
- Regelmäßige Prüfung mit konfigurierbarem Intervall
- Benachrichtigungen über neue Anzeigen im Matrix-Raum
- Unterstützung mehrerer Räume — jeder Raum hat eigene Suchaufträge
- Basierend auf [matrix-nio](https://github.com/poljar/matrix-nio)

## Schnellstart

### 1. Matrix-Konto für den Bot erstellen

Registriere einen eigenen Benutzer auf einem beliebigen Homeserver (matrix.org, eigener Server usw.).

### 2. Klonen und konfigurieren

```bash
git clone <repo-url> && cd matrix-kleinanzeigen-bot
cp .env.example .env
```

Bearbeite `.env` mit den Zugangsdaten des Bots.

### 3. Starten

**Docker:**
```bash
docker compose up -d
```

**Lokal:**
```bash
pip install -r requirements.txt
python main.py
```

### 4. Bot in einen Raum einladen

Lade `@your-bot:matrix.org` in einen Matrix-Raum ein. Der Bot nimmt Einladungen automatisch an.

## Befehle

| Befehl | Beschreibung |
|---|---|
| `!add <url> [Name]` | Suchauftrag hinzufügen. URL ist eine Kleinanzeigen-Suchergebnisseite |
| `!remove <id>` | Suchauftrag anhand der ID entfernen |
| `!list` | Alle Suchaufträge in diesem Raum anzeigen |
| `!check` | Sofortige Prüfung erzwingen |
| `!help` | Hilfe anzeigen |

## Beispiel

```
!add https://www.kleinanzeigen.de/s-fahrraeder/berlin/k0c217 Fahrräder Berlin
✅ Suche #1 hinzugefügt: Fahrräder Berlin

-- 10 Minuten später --

**Neue Anzeigen für «Fahrräder Berlin»**

• [Trek Domane AL 2 2023](https://...) — *750 €*
  _Berlin, Mitte_
• [Canyon Endurace CF SL](https://...) — *1.200 € VB*
  _Berlin, Prenzlauer Berg_
```

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `MATRIX_HOMESERVER` | `https://matrix.org` | Homeserver des Bots |
| `MATRIX_USER` | — | Vollständige MXID-Anmeldung |
| `MATRIX_PASSWORD` | — | Passwort |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/kleinanzeigen.db` | Datenbankpfad |
| `CHECK_INTERVAL` | `600` | Prüfintervall in Sekunden |

## Haftungsausschluss

Der automatisierte Zugriff auf kleinanzeigen.de kann gegen die Nutzungsbedingungen verstoßen (§ 5 der [Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/)). Die Entwickler übernehmen keinerlei Haftung für mögliche Schäden oder rechtliche Konsequenzen. Die Nutzung erfolgt auf eigenes Risiko.

## Lizenz

MIT
