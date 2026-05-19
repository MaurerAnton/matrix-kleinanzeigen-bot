import logging

import aiohttp

from .models import AdItem, ScrapeResult

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def scrape(
    session: aiohttp.ClientSession, url: str, recursive: bool = False
) -> ScrapeResult:
    result = ScrapeResult(url=url)

    try:
        async with session.get(
            url, headers={"User-Agent": USER_AGENT}
        ) as resp:
            if resp.status == 200:
                text = await resp.text()
                if "api.leboncoin.fr" in text or "__NEXT" in text:
                    result.error = (
                        "Leboncoin uses JavaScript rendering. "
                        "The search results are loaded via API calls, "
                        "not available in plain HTML. "
                        "See docs for headless browser setup."
                    )
                else:
                    result.error = (
                        f"Leboncoin returned unexpected content (status {resp.status})."
                    )
            elif resp.status == 403:
                result.error = (
                    "Leboncoin blocked the request (DataDome/WAF). "
                    "The search API is protected by bot detection."
                )
            else:
                result.error = f"HTTP {resp.status}"

    except Exception as e:
        logger.exception("Leboncoin scrape error: %s", e)
        result.error = str(e)

    return result
