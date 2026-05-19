import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    room_id = Column(String, unique=True, nullable=False)

    searches = relationship("Search", back_populates="room", cascade="all, delete-orphan")


class Search(Base):
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    last_check = Column(DateTime, nullable=True)

    room = relationship("Room", back_populates="searches")
    posts = relationship("AdPost", back_populates="search", cascade="all, delete-orphan")


class AdPost(Base):
    __tablename__ = "ad_posts"

    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    ad_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(String, nullable=True)
    url = Column(String, nullable=False)
    location = Column(String, nullable=True)
    is_top_ad = Column(Boolean, default=False)
    found_at = Column(DateTime, default=datetime.datetime.utcnow)

    search = relationship("Search", back_populates="posts")
