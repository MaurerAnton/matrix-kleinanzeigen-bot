import logging
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from .models import AdItem, ScrapeResult
from .config import SCRAPINGBEE_API_KEY

logger = logging.getLogger(__name__)

SCRAPINGBEE_URL = "https://app.scrapingbee.com/api/v1/"


async def scrape(
    session: aiohttp.ClientSession, url: str, recursive: bool = False
) -> ScrapeResult:
    result = ScrapeResult(url=url)

    try:
        html = await _fetch_page(session, url)
        if html is None:
            result.error = (
                "Leboncoin blocked the request (DataDome/WAF). "
                "Set SCRAPINGBEE_API_KEY in .env for JS rendering."
            )
            return result

        soup = BeautifulSoup(html, "html.parser")
        items = _parse_ad_items(soup, url)
        result.ad_items = items
        logger.info("Leboncoin: scraped %d items from %s", len(items), url)

        if not items:
            result.error = (
                "No listings found. The page layout may have changed "
                "or the URL is invalid."
            )

    except Exception as e:
        logger.exception("Leboncoin scrape error: %s", e)
        result.error = str(e)

    return result


async def _fetch_page(
    session: aiohttp.ClientSession, url: str
) -> str | None:
    if SCRAPINGBEE_API_KEY:
        return await _fetch_scrapingbee(session, url)
    return await _fetch_direct(session, url)


async def _fetch_scrapingbee(
    session: aiohttp.ClientSession, url: str
) -> str | None:
    params = {
        "api_key": SCRAPINGBEE_API_KEY,
        "url": url,
        "render_js": "true",
        "country_code": "fr",
        "wait": "3000",
        "block_resources": "false",
    }
    try:
        async with session.get(
            SCRAPINGBEE_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.warning(
                    "Scrapingbee error %d: %s", resp.status, text[:300]
                )
                return None
            return await resp.text()
    except Exception as e:
        logger.error("Scrapingbee request failed: %s", e)
        return None


async def _fetch_direct(
    session: aiohttp.ClientSession, url: str
) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    try:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status != 200:
                logger.warning("Leboncoin HTTP %d for %s", resp.status, url)
                return None
            return await resp.text()
    except Exception as e:
        logger.error("Leboncoin direct request failed: %s", e)
        return None


def _parse_ad_items(soup: BeautifulSoup, base_url: str) -> list[AdItem]:
    items = []

    # Leboncoin renders ad cards as <a> links with href containing /ad/
    ad_links = soup.select('a[href*="/ad/"]')
    for link in ad_links:
        try:
            href = link.get("href", "")
            if not href or "/ad/" not in href:
                continue

            item_url = urljoin(base_url, href)
            ad_id = href.rstrip("/").split("/")[-1]
            if not ad_id or "." in ad_id:
                ad_id = href.strip("/").replace("/", "-")

            title = _get_text(link, "h2, h3, [class*=title], p")
            if not title:
                continue

            price = _get_text(link, "[class*=price], [class*=Price], span")
            if not price or "\u20ac" not in price:
                for el in link.select("*"):
                    txt = el.get_text(strip=True)
                    if "\u20ac" in txt and len(txt) < 60:
                        price = txt
                        break

            location = _get_text(link, "[class*=location], [class*=city], [class*=place]")

            items.append(AdItem(
                id=ad_id,
                url=item_url,
                title=title,
                price=price or "",
                description="",
                location=location or "",
                is_top_ad=False,
            ))
        except Exception as e:
            logger.debug("Error parsing leboncoin ad: %s", e)

    if not items:
        for article in soup.select("article, [data-test-id]"):
            title = article.get_text(strip=True)[:100]
            if title:
                logger.debug("Found element: %s", title[:80])

    return items


def _get_text(soup, selector: str) -> str:
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else ""
