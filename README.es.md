# Kleinanzeigen Matrix Bot

Un bot de Matrix que monitorea nuevos anuncios en [kleinanzeigen.de](https://kleinanzeigen.de) y envía notificaciones a salas de Matrix.

[English](README.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

## Funcionalidades

- Monitoreo de búsquedas de Kleinanzeigen por URL
- Verificaciones periódicas con intervalo configurable
- Notificaciones de nuevos anuncios en salas de Matrix
- Soporte multisala: cada sala tiene sus propias búsquedas
- Basado en [matrix-nio](https://github.com/poljar/matrix-nio)

## Inicio rápido

### 1. Crear una cuenta de Matrix para el bot

Registra un usuario separado en cualquier servidor (matrix.org, propio, etc.).

### 2. Clonar y configurar

```bash
git clone <repo-url> && cd matrix-kleinanzeigen-bot
cp .env.example .env
```

Edita `.env` con las credenciales del bot.

### 3. Ejecutar

**Docker:**
```bash
docker compose up -d
```

**Local:**
```bash
pip install -r requirements.txt
python main.py
```

### 4. Invitar al bot a una sala

Invita a `@your-bot:matrix.org` a cualquier sala de Matrix. El bot acepta invitaciones automáticamente.

## Comandos

| Comando | Descripción |
|---|---|
| `!add <url> [nombre]` | Agregar una búsqueda. La URL es una página de resultados de Kleinanzeigen |
| `!remove <id>` | Eliminar una búsqueda por ID |
| `!list` | Mostrar todas las búsquedas en esta sala |
| `!check` | Forzar una verificación inmediata |
| `!help` | Mostrar ayuda |

## Ejemplo

```
!add https://www.kleinanzeigen.de/s-bicicletas/berlin/k0c217 Bicicletas Berlín
✅ Búsqueda #1 agregada: Bicicletas Berlín

-- 10 minutos después --

**Nuevos anuncios para «Bicicletas Berlín»**

• [Trek Domane AL 2 2023](https://...) — *750 €*
  _Berlín, Mitte_
• [Canyon Endurace CF SL](https://...) — *1.200 €*
  _Berlín, Prenzlauer Berg_
```

## Variables de entorno

| Variable | Predeterminado | Descripción |
|---|---|---|
| `MATRIX_HOMESERVER` | `https://matrix.org` | Servidor Matrix del bot |
| `MATRIX_USER` | — | Inicio de sesión MXID completo |
| `MATRIX_PASSWORD` | — | Contraseña |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/kleinanzeigen.db` | Ruta de la base de datos |
| `CHECK_INTERVAL` | `600` | Intervalo de verificación en segundos |

## Aviso legal

El acceso automatizado a kleinanzeigen.de puede infringir sus condiciones de uso (artículo 5 de los [Nutzungsbedingungen](https://themen.kleinanzeigen.de/nutzungsbedingungen/)). Los desarrolladores no asumen ninguna responsabilidad por daños o consecuencias legales. Úsalo bajo tu propio riesgo.

## Licencia

MIT
