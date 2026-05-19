import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class AdItem:
    id: str
    url: str
    title: str
    description: str = ""
    location: str = ""
    price: str = ""
    is_top_ad: bool = False
    image_url: Optional[str] = None


@dataclass
class ScrapeResult:
    url: str
    ad_items: list[AdItem] = field(default_factory=list)
    error: Optional[str] = None


async def get_soup(session: aiohttp.ClientSession, url: str) -> Optional[BeautifulSoup]:
    try:
        async with session.get(url, headers={"User-Agent": USER_AGENT}) as resp:
            if resp.status != 200:
                logger.warning("HTTP %d for %s", resp.status, url)
                return None
            text = await resp.text()
            return BeautifulSoup(text, "html.parser")
    except Exception as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return None


def parse_ad_items(soup: BeautifulSoup, base_url: str) -> list[AdItem]:
    items = []
    for article in soup.find_all("article", class_="aditem"):
        try:
            ad_id = article.get("data-adid", "")
            if not ad_id:
                continue

            link = article.get("data-href", "")
            if not link:
                a_tag = article.find("a", class_="ellipsis")
                link = a_tag.get("href", "") if a_tag else ""

            item_url = urljoin(base_url, link) if link else ""

            title_el = article.find(class_="ellipsis")
            title = title_el.get_text(strip=True) if title_el else "No title"

            price_el = article.find(
                class_="aditem-main--middle--price-shipping--price"
            )
            price = price_el.get_text(strip=True) if price_el else ""

            desc_el = article.find(class_="aditem-main--middle--description")
            description = desc_el.get_text(strip=True) if desc_el else ""

            location_el = article.find(class_="aditem-main--top--left")
            location = location_el.get_text(" ", strip=True) if location_el else ""

            is_top = "is-topad" in (article.get("class") or [])

            img_el = article.find("img")
            image_url = img_el.get("src") if img_el else None

            items.append(AdItem(
                id=ad_id,
                url=item_url,
                title=title,
                description=description,
                location=location,
                price=price,
                is_top_ad=is_top,
                image_url=image_url,
            ))
        except Exception as e:
            logger.exception("Error parsing ad item: %s", e)
    return items


def get_pagination_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    urls = []
    for a in soup.select("a.pagination-page"):
        href = a.get("href")
        if href:
            urls.append(urljoin(base_url, href))
    return urls


async def scrape_url(
    session: aiohttp.ClientSession, url: str, recursive: bool = False
) -> ScrapeResult:
    result = ScrapeResult(url=url)
    soup = await get_soup(session, url)
    if soup is None:
        result.error = "Failed to fetch page"
        return result

    result.ad_items = parse_ad_items(soup, url)

    if recursive:
        for page_url in get_pagination_urls(soup, url):
            page_soup = await get_soup(session, page_url)
            if page_soup:
                result.ad_items.extend(parse_ad_items(page_soup, page_url))

    logger.info("Scraped %d items from %s", len(result.ad_items), url)
    return result
