import datetime
import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Room, Search, AdPost, BlockedWord

logger = logging.getLogger(__name__)


async def get_or_create_room(session: AsyncSession, room_id: str) -> Room:
    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one_or_none()
    if room is None:
        room = Room(room_id=room_id)
        session.add(room)
        await session.commit()
        await session.refresh(room)
    return room


async def add_search(
    session: AsyncSession, room: Room, url: str, name: str
) -> Search:
    s = Search(room_id=room.id, url=url, name=name)
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return s


async def get_searches(session: AsyncSession, room: Room) -> Sequence[Search]:
    result = await session.execute(
        select(Search).where(Search.room_id == room.id)
    )
    return result.scalars().all()


async def get_search_by_id(session: AsyncSession, search_id: int) -> Search | None:
    result = await session.execute(select(Search).where(Search.id == search_id))
    return result.scalar_one_or_none()


async def remove_search(session: AsyncSession, search: Search) -> None:
    await session.delete(search)
    await session.commit()


async def ad_exists(session: AsyncSession, search_id: int, ad_id: str) -> bool:
    result = await session.execute(
        select(AdPost).where(
            AdPost.search_id == search_id, AdPost.ad_id == ad_id
        )
    )
    return result.scalar_one_or_none() is not None


async def save_ad(session: AsyncSession, search_id: int, ad: "AdItem") -> AdPost:
    from .models import AdItem
    post = AdPost(
        search_id=search_id,
        ad_id=ad.id,
        title=ad.title,
        price=ad.price,
        url=ad.url,
        location=ad.location,
        is_top_ad=ad.is_top_ad,
    )
    session.add(post)
    return post


async def mark_search_checked(session: AsyncSession, search: Search) -> None:
    search.last_check = datetime.datetime.utcnow()
    session.add(search)
    await session.commit()


async def set_eval_prompt(
    session: AsyncSession, search: Search, prompt: str
) -> None:
    search.eval_prompt = prompt
    session.add(search)
    await session.commit()


async def get_all_searches_for_all_rooms(
    session: AsyncSession,
) -> list[tuple[Room, Search]]:
    result = await session.execute(select(Search).join(Room))
    searches = result.scalars().all()
    pairs = []
    for s in searches:
        room = await session.get(Room, s.room_id)
        pairs.append((room, s))
    return pairs


async def add_blocked_word(
    session: AsyncSession, room: Room, word: str
) -> BlockedWord:
    bw = BlockedWord(room_id=room.id, word=word.lower())
    session.add(bw)
    await session.commit()
    return bw


async def get_blocked_words(
    session: AsyncSession, room: Room
) -> Sequence[BlockedWord]:
    result = await session.execute(
        select(BlockedWord).where(BlockedWord.room_id == room.id)
    )
    return result.scalars().all()


async def get_blocked_word(
    session: AsyncSession, room: Room, word: str
) -> BlockedWord | None:
    result = await session.execute(
        select(BlockedWord).where(
            BlockedWord.room_id == room.id,
            BlockedWord.word == word.lower(),
        )
    )
    return result.scalar_one_or_none()


async def remove_blocked_word(
    session: AsyncSession, bw: BlockedWord
) -> None:
    await session.delete(bw)
    await session.commit()


async def title_is_blocked(
    session: AsyncSession, room: Room, title: str
) -> bool:
    words = await get_blocked_words(session, room)
    title_lower = title.lower()
    return any(w.word in title_lower for w in words)
