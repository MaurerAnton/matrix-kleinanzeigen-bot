import asyncio
import logging
import re
import shlex
from pathlib import Path

import aiohttp
from nio import (
    AsyncClient,
    MatrixRoom,
    RoomMessageText,
    InviteMemberEvent,
)

from .config import MATRIX_HOMESERVER, MATRIX_USER, MATRIX_PASSWORD, MATRIX_ACCESS_TOKEN, CHECK_INTERVAL
from .db import async_session, init_db
from .scraper import scrape_url
from . import crud
from .models import build_kleinanzeigen_url
from .llm import evaluate_listing
from .config import LLM_PROVIDER, LLM_MODEL

logger = logging.getLogger(__name__)
CRYPTO_STORE_DIR = Path("data/crypto_store")

DISCLAIMER = (
    "Automated access to kleinanzeigen.de may violate their Terms of Service "
    "(Section 5 of the Nutzungsbedingungen). "
    "The developers assume no liability for any damages or legal consequences. "
    "Use at your own risk."
)

HELP_TEXT = (
    "Kleinanzeigen / Leboncoin Matrix Bot\n"
    "\n"
    "!search <query> [city] [min] [max]\n"
    "                    search Kleinanzeigen by keywords\n"
    "!add <url> [name]   add a search by URL\n"
    "!remove <id>        remove a search by ID\n"
    "!list               show all searches in this room\n"
    "!check              force an immediate check\n"
    "!block <word>       hide listings containing this word\n"
    "!unblock <word>     stop blocking a word\n"
    "!blocks             show blocked words\n"
    "!eval <id> <prompt> set LLM evaluation prompt for a search\n"
    "!evaloff <id>       disable LLM evaluation for a search\n"
    "!evalmodel          show current LLM provider/model\n"
    "!disclaimer         show legal disclaimer\n"
    "!help               show this help\n"
    "\n"
    "LLM evaluation requires LLM_API_KEY (or Ollama) in .env\n"
    "\n"
    + DISCLAIMER
)


class KleinanzeigenBot:
    def __init__(self):
        self.client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER)
        self.session: aiohttp.ClientSession | None = None
        self._disclaimed_rooms: set[str] = set()
        self._e2ee_enabled = False

    async def _setup_crypto(self):
        try:
            from nio.crypto import ENCRYPTION_ENABLED
            if ENCRYPTION_ENABLED:
                from nio.store import SqliteStore
                CRYPTO_STORE_DIR.mkdir(parents=True, exist_ok=True)
                self.client.store = SqliteStore(
                    self.client.user_id,
                    "",  # device_id auto-assigned
                    str(CRYPTO_STORE_DIR),
                )
                self.client.store.load_account()
                self.client.store.load_device_keys()
                self._e2ee_enabled = True
                logger.info(
                    "E2EE enabled (store: %s)", CRYPTO_STORE_DIR
                )
            else:
                logger.info("E2EE not available (python-olm missing)")
        except Exception as e:
            logger.warning("Failed to setup E2EE: %s", e)

    async def start(self):
        await init_db()
        if MATRIX_ACCESS_TOKEN:
            logger.info("Restoring session on %s as %s", MATRIX_HOMESERVER, MATRIX_USER)
            self.client.access_token = MATRIX_ACCESS_TOKEN
            self.client.user_id = MATRIX_USER
        else:
            logger.info("Logging in to %s as %s", MATRIX_HOMESERVER, MATRIX_USER)
            await self.client.login(MATRIX_PASSWORD)

        await self._setup_crypto()

        self.client.add_event_callback(self._on_message, RoomMessageText)
        self.client.add_event_callback(self._on_invite, InviteMemberEvent)

        self.session = aiohttp.ClientSession()
        asyncio.create_task(self._scraper_loop())

        logger.info("Bot started. Syncing...")
        await self._sync_loop()

    async def _sync_loop(self):
        next_batch = None
        while True:
            try:
                sync = await self.client.sync(
                    timeout=30000, since=next_batch
                )
                if sync and hasattr(sync, "next_batch"):
                    next_batch = sync.next_batch or next_batch
            except AssertionError:
                logger.debug("Sync assertion (progressive.chat quirk) – continuing")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(
                    "Sync error (type=%s). Retrying in 10s...",
                    type(e).__name__,
                )
                await asyncio.sleep(10)

    async def _on_invite(self, room: MatrixRoom, event: InviteMemberEvent):
        if event.state_key != self.client.user_id:
            return
        try:
            await self.client.join(room.room_id)
            logger.info("Joined room %s", room.room_id)
        except Exception as e:
            logger.error("Failed to join %s: %s", room.room_id, e)

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText):
        if event.sender == self.client.user_id:
            return
        await self._handle_message(room, event)

    async def _handle_message(self, room: MatrixRoom, event: RoomMessageText):

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

            elif cmd == "!search":
                await self._cmd_search(db, room, db_room, args)

            elif cmd == "!add":
                await self._cmd_add(db, room, db_room, args)

            elif cmd == "!remove":
                await self._cmd_remove(db, room, db_room, args)

            elif cmd == "!list":
                await self._cmd_list(db, room, db_room)

            elif cmd == "!check":
                await self._reply(room, "Running check...")
                await self._check_all(db)

            elif cmd == "!block":
                await self._cmd_block(db, room, db_room, args)

            elif cmd == "!unblock":
                await self._cmd_unblock(db, room, db_room, args)

            elif cmd == "!blocks":
                await self._cmd_blocks(db, room, db_room)

            elif cmd == "!eval":
                await self._cmd_eval(db, room, db_room, args)

            elif cmd == "!evaloff":
                await self._cmd_evaloff(db, room, db_room, args)

            elif cmd == "!evalmodel":
                await self._cmd_evalmodel(room)

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

        if "kleinanzeigen.de" not in url and "leboncoin.fr" not in url:
            await self._reply(
                room,
                "Unsupported site. Currently supported: "
                "kleinanzeigen.de, leboncoin.fr",
            )
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

    async def _cmd_search(self, db, room, db_room, args):
        if not args:
            await self._reply(
                room,
                "Usage: !search <keyword> [city] [min_price] [max_price]\n"
                "Example: !search iphone berlin 100 500",
            )
            return

        query = args[0]
        city = args[1] if len(args) > 1 else ""
        min_price = args[2] if len(args) > 2 else ""
        max_price = args[3] if len(args) > 3 else ""

        url = build_kleinanzeigen_url(query, city, min_price, max_price)
        name = query
        if city:
            name += f" ({city})"

        await self._reply(
            room, f"Searching for **{name}** ...\n{url}"
        )

        result = await scrape_url(self.session, url)
        if result.error:
            await self._reply(
                room, f"Error: {result.error}"
            )
            return

        if not result.ad_items:
            await self._reply(room, "No listings found.")
            return

        blocked = await crud.get_blocked_words(db, db_room)
        blocked_words = [w.word for w in blocked]

        visible = [
            ad for ad in result.ad_items
            if not any(bw in ad.title.lower() for bw in blocked_words)
        ]

        lines = [
            f"**Search results for \u00ab{name}\u00bb**",
            f"Found {len(visible)} listings",
            f"",
        ]
        limit = min(len(visible), 15)
        for ad in visible[:limit]:
            price_str = f"**{ad.price}**" if ad.price else "**? EUR**"
            lines.append(
                f"\u2022 [{ad.title}]({ad.url}) \u2014 {price_str}"
            )
            if ad.location:
                lines.append(f"  _{ad.location}_")

        if len(visible) > limit:
            lines.append(f"_...and {len(visible) - limit} more_")

        if blocked_words:
            hidden = len(result.ad_items) - len(visible)
            if hidden > 0:
                lines.append(
                    f"_({hidden} hidden by blocked words: "
                    + ", ".join(blocked_words) + ")_"
                )

        await self._reply(room, "\n".join(lines))

        search = await crud.add_search(db, db_room, url, name)
        self._disclaimed_rooms.add(room.room_id)
        await self._reply(
            room,
            f"Ongoing monitoring added as search #{search.id}. "
            f"Use `!remove {search.id}` to stop.",
        )

    async def _cmd_block(self, db, room, db_room, args):
        if not args:
            await self._reply(room, "Usage: !block <word>")
            return
        word = args[0]
        existing = await crud.get_blocked_word(db, db_room, word)
        if existing:
            await self._reply(room, f"Word **{word}** is already blocked.")
            return
        await crud.add_blocked_word(db, db_room, word)
        await self._reply(room, f"Blocked word: **{word}**")

    async def _cmd_unblock(self, db, room, db_room, args):
        if not args:
            await self._reply(room, "Usage: !unblock <word>")
            return
        word = args[0]
        bw = await crud.get_blocked_word(db, db_room, word)
        if not bw:
            await self._reply(room, f"Word **{word}** is not blocked.")
            return
        await crud.remove_blocked_word(db, bw)
        await self._reply(room, f"Unblocked: **{word}**")

    async def _cmd_blocks(self, db, room, db_room):
        words = await crud.get_blocked_words(db, db_room)
        if not words:
            await self._reply(room, "No blocked words.")
            return
        lines = ["**Blocked words:**"]
        for w in words:
            lines.append(f"  \u2022 {w.word}")
        await self._reply(room, "\n".join(lines))

    async def _cmd_eval(self, db, room, db_room, args):
        if len(args) < 2:
            await self._reply(
                room,
                "Usage: !eval <search_id> <prompt>\n"
                "Example: !eval 1 Is this a good price for a used iPhone? "
                "Check for scratches and battery health.",
            )
            return
        try:
            sid = int(args[0])
        except ValueError:
            await self._reply(room, "Search ID must be a number.")
            return

        search = await crud.get_search_by_id(db, sid)
        if search is None or search.room_id != db_room.id:
            await self._reply(room, f"Search #{sid} not found.")
            return

        prompt = " ".join(args[1:])
        await crud.set_eval_prompt(db, search, prompt)
        await self._reply(
            room,
            f"LLM evaluation enabled for search #{sid}: **{search.name}**\n"
            f"Prompt: _{prompt}_",
        )

    async def _cmd_evaloff(self, db, room, db_room, args):
        if not args:
            await self._reply(room, "Usage: !evaloff <search_id>")
            return
        try:
            sid = int(args[0])
        except ValueError:
            await self._reply(room, "Search ID must be a number.")
            return

        search = await crud.get_search_by_id(db, sid)
        if search is None or search.room_id != db_room.id:
            await self._reply(room, f"Search #{sid} not found.")
            return

        await crud.set_eval_prompt(db, search, None)
        await self._reply(room, f"LLM evaluation disabled for search #{sid}.")

    async def _cmd_evalmodel(self, room):
        if not LLM_PROVIDER:
            await self._reply(
                room,
                "LLM not configured. Set LLM_PROVIDER, LLM_API_KEY (or use Ollama) in .env\n"
                "Supported: openai, anthropic, ollama",
            )
            return
        model = LLM_MODEL or "default"
        await self._reply(
            room,
            f"LLM provider: **{LLM_PROVIDER}**\n"
            f"Model: **{model}**",
        )

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
                    filtered = [
                        ad for ad in new_items
                        if not await crud.title_is_blocked(db, room, ad.title)
                    ]
                    if filtered:
                        evaluations = {}
                        if search.eval_prompt:
                            for ad in filtered[:3]:
                                try:
                                    ev = await evaluate_listing(
                                        ad.title, ad.price,
                                        ad.description, ad.location,
                                        search.eval_prompt,
                                    )
                                    if ev:
                                        evaluations[ad.id] = ev
                                except Exception as e:
                                    logger.debug("LLM eval error: %s", e)
                        await self._notify(
                            room.room_id, search, filtered, evaluations
                        )
                    logger.info(
                        "Search #%d: %d new, %d after block filter",
                        search.id, len(new_items), len(filtered),
                    )
            except Exception as e:
                logger.exception(
                    "Error checking search #%d: %s", search.id, e
                )

    async def _notify(self, room_id: str, search, items, evaluations=None):
        if evaluations is None:
            evaluations = {}
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
            if ad.id in evaluations:
                lines.append(f"  _\U0001f916 {evaluations[ad.id]}_")

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
