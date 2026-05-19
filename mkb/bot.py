import asyncio
import logging
import re
import shlex

import aiohttp
from nio import (
    AsyncClient,
    MatrixRoom,
    RoomMessageText,
)

from .config import MATRIX_HOMESERVER, MATRIX_USER, MATRIX_PASSWORD, CHECK_INTERVAL
from .db import async_session, init_db
from .scraper import scrape_url
from . import crud

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Automated access to kleinanzeigen.de may violate their Terms of Service "
    "(Section 5 of the Nutzungsbedingungen). "
    "The developers assume no liability for any damages or legal consequences. "
    "Use at your own risk."
)

HELP_TEXT = (
    "Kleinanzeigen Matrix Bot\n"
    "\n"
    "!add <url> [name]   add a search by URL\n"
    "!remove <id>        remove a search by ID\n"
    "!list               show all searches in this room\n"
    "!check              force an immediate check\n"
    "!disclaimer         show legal disclaimer\n"
    "!help               show this help\n"
    "\n"
    + DISCLAIMER
)


class KleinanzeigenBot:
    def __init__(self):
        self.client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER)
        self.session: aiohttp.ClientSession | None = None
        self._disclaimed_rooms: set[str] = set()

    async def start(self):
        await init_db()
        logger.info("Logging in to %s as %s", MATRIX_HOMESERVER, MATRIX_USER)
        await self.client.login(MATRIX_PASSWORD)

        self.client.add_event_callback(self._on_message, RoomMessageText)

        self.session = aiohttp.ClientSession()
        asyncio.create_task(self._scraper_loop())

        logger.info("Bot started. Syncing...")
        await self.client.sync_forever(timeout=30000)

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText):
        if event.sender == self.client.user_id:
            return

        body = event.body.strip()
        if not body.startswith("!"):
            return

        try:
            parts = shlex.split(body)
        except ValueError:
            parts = body.split()

        cmd = parts[0].lower()
        args = parts[1:]

        async with async_session() as db:
            db_room = await crud.get_or_create_room(db, room.room_id)

            if cmd == "!help":
                await self._reply(room, HELP_TEXT)

            elif cmd == "!disclaimer":
                await self._reply(room, DISCLAIMER)

            elif cmd == "!add":
                await self._cmd_add(db, room, db_room, args)

            elif cmd == "!remove":
                await self._cmd_remove(db, room, db_room, args)

            elif cmd == "!list":
                await self._cmd_list(db, room, db_room)

            elif cmd == "!check":
                await self._reply(room, "Running check...")
                await self._check_all(db)

            else:
                await self._reply(room, f"Unknown command: {cmd}\n{HELP_TEXT}")

    async def _require_disclaimer(self, db, room, db_room) -> bool:
        if room.room_id in self._disclaimed_rooms:
            return True
        searches = await crud.get_searches(db, db_room)
        if len(searches) > 0:
            self._disclaimed_rooms.add(room.room_id)
            return True
        await self._reply(room, DISCLAIMER)
        await self._reply(
            room,
            "To confirm you understand the risks, type `!add <url>` again "
            "or `!disclaimer` to read the notice.",
        )
        return False

    async def _cmd_add(self, db, room, db_room, args):
        if not args:
            await self._reply(room, "Usage: !add <url> [name]")
            return

        url = args[0]
        name = args[1] if len(args) > 1 else (
            url.split("/")[-2] if "/" in url else "Search"
        )

        if "kleinanzeigen.de" not in url:
            await self._reply(room, "This does not look like a Kleinanzeigen URL.")
            return

        search = await crud.add_search(db, db_room, url, name)
        self._disclaimed_rooms.add(room.room_id)
        await self._reply(
            room, f"Added search #{search.id}: **{name}**\n{url}"
        )

    async def _cmd_remove(self, db, room, db_room, args):
        if not args:
            await self._reply(room, "Usage: !remove <id>")
            return
        try:
            sid = int(args[0])
        except ValueError:
            await self._reply(room, "ID must be a number.")
            return

        search = await crud.get_search_by_id(db, sid)
        if search is None or search.room_id != db_room.id:
            await self._reply(room, f"Search #{sid} not found.")
            return

        await crud.remove_search(db, search)
        await self._reply(room, f"Search #{sid} removed.")

    async def _cmd_list(self, db, room, db_room):
        searches = await crud.get_searches(db, db_room)
        if not searches:
            await self._reply(
                room, "No active searches. Add one with `!add <url>`."
            )
            return

        lines = ["**Active searches:**"]
        for s in searches:
            last = (
                s.last_check.strftime("%H:%M %d.%m")
                if s.last_check
                else "never"
            )
            lines.append(f"  #{s.id} — {s.name} (last: {last})")
        await self._reply(room, "\n".join(lines))

    async def _scraper_loop(self):
        while True:
            await asyncio.sleep(CHECK_INTERVAL)
            try:
                async with async_session() as db:
                    await self._check_all(db)
            except Exception as e:
                logger.exception("Scraper loop error: %s", e)

    async def _check_all(self, db):
        pairs = await crud.get_all_searches_for_all_rooms(db)
        if not pairs:
            return

        logger.info("Checking %d searches...", len(pairs))

        for room, search in pairs:
            try:
                result = await scrape_url(self.session, search.url)
                if result.error:
                    logger.warning(
                        "Scrape error for %s: %s", search.url, result.error
                    )
                    continue

                new_items = []
                for ad in result.ad_items:
                    if not await crud.ad_exists(db, search.id, ad.id):
                        await crud.save_ad(db, search.id, ad)
                        new_items.append(ad)

                await crud.mark_search_checked(db, search)

                if new_items:
                    await self._notify(room.room_id, search, new_items)
                    logger.info(
                        "Search #%d: %d new items", search.id, len(new_items)
                    )
            except Exception as e:
                logger.exception(
                    "Error checking search #%d: %s", search.id, e
                )

    async def _notify(self, room_id: str, search, items):
        lines = [
            f"**New listings for \u00ab{search.name}\u00bb**",
            "",
        ]

        limit = min(len(items), 10)
        for ad in items[:limit]:
            price_str = f"**{ad.price}**" if ad.price else "**? EUR**"
            lines.append(
                f"\u2022 [{ad.title}]({ad.url}) \u2014 {price_str}"
            )
            if ad.location:
                lines.append(f"  _{ad.location}_")

        if len(items) > limit:
            lines.append("")
            lines.append(f"_...and {len(items) - limit} more_")

        content = {
            "msgtype": "m.text",
            "body": "\n".join(lines),
            "format": "org.matrix.custom.html",
            "formatted_body": self._md_to_html("\n".join(lines)),
        }

        try:
            await self.client.room_send(room_id, "m.room.message", content)
        except Exception as e:
            logger.error(
                "Failed to send notification to %s: %s", room_id, e
            )

    async def _reply(self, room: MatrixRoom, text: str):
        content = {
            "msgtype": "m.text",
            "body": text,
            "format": "org.matrix.custom.html",
            "formatted_body": self._md_to_html(text),
        }
        await self.client.room_send(room.room_id, "m.room.message", content)

    @staticmethod
    def _md_to_html(text: str) -> str:
        html = text
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)
        html = html.replace("\n", "<br>")
        return html
