# Kleinanzeigen Matrix Bot

Un bot Matrix qui surveille les nouvelles annonces sur [kleinanzeigen.de](https://kleinanzeigen.de) et envoie des notifications dans les salons Matrix.

[English](README.md) | [Deutsch](README.de.md) | [Español](README.es.md)

## Fonctionnalités

- Surveillance des recherches Kleinanzeigen par URL
- Vérifications périodiques avec intervalle configurable
- Notifications des nouvelles annonces dans les salons Matrix
- Support multi-salons : chaque salon a ses propres recherches
- Basé sur [matrix-nio](https://github.com/poljar/matrix-nio)

## Démarrage rapide

### 1. Créer un compte Matrix pour le bot

Enregistre un utilisateur séparé sur n'importe quel serveur Matrix (matrix.org, auto-hébergé, etc.).

### 2. Cloner et configurer

```bash
git clone <repo-url> && cd matrix-kleinanzeigen-bot
cp .env.example .env
```

Édite `.env` avec les identifiants du bot.

### 3. Lancer

**Docker :**
```bash
docker compose up -d
```

**Local :**
```bash
pip install -r requirements.txt
python main.py
```

### 4. Inviter le bot dans un salon

Invite `@your-bot:matrix.org` dans un salon Matrix. Le bot accepte les invitations automatiquement.

## Commandes

| Commande | Description |
|---|---|
| `!add <url> [nom]` | Ajouter une recherche. L'URL est une page de résultats Kleinanzeigen |
| `!remove <id>` | Supprimer une recherche par ID |
| `!list` | Afficher toutes les recherches dans ce salon |
| `!check` | Forcer une vérification immédiate |
| `!help` | Afficher l'aide |

## Exemple

```
!add https://www.kleinanzeigen.de/s-velos/berlin/k0c217 Vélos Berlin
✅ Recherche #1 ajoutée : Vélos Berlin

-- 10 minutes plus tard --

**Nouvelles annonces pour « Vélos Berlin »**

• [Trek Domane AL 2 2023](https://...) — *750 €*
  _Berlin, Mitte_
• [Canyon Endurace CF SL](https://...) — *1 200 €*
  _Berlin, Prenzlauer Berg_
```

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `MATRIX_HOMESERVER` | `https://matrix.org` | Serveur Matrix du bot |
| `MATRIX_USER` | — | Identifiant MXID complet |
| `MATRIX_PASSWORD` | — | Mot de passe |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/kleinanzeigen.db` | Chemin de la base de données |
| `CHECK_INTERVAL` | `600` | Intervalle de vérification en secondes |

## Avertissement

L'accès automatisé à kleinanzeigen.de peut enfreindre leurs conditions d'utilisation (article 5 des [Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/)). Les développeurs déclinent toute responsabilité pour tout dommage ou conséquence juridique. À utiliser à vos propres risques.

## Licence

MIT
