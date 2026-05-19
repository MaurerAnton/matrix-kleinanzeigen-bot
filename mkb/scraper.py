import logging

import aiohttp

from . import kleinanzeigen
from . import leboncoin
from .models import AdItem, ScrapeResult

logger = logging.getLogger(__name__)


async def scrape_url(
    session: aiohttp.ClientSession, url: str, recursive: bool = False
) -> ScrapeResult:
    if "kleinanzeigen.de" in url:
        return await kleinanzeigen.scrape(session, url, recursive)
    elif "leboncoin.fr" in url:
        return await leboncoin.scrape(session, url, recursive)
    else:
        return ScrapeResult(url=url, error=f"unsupported site: {url}")
