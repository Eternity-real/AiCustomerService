from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    session_uuid = Column(String(36), nullable=False, unique=True)
    title = Column(String(200))
    status = Column(Enum('active', 'closed'), default='active')
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # relationships
    user = relationship('User', back_populates='sessions')
    messages = relationship('Message', back_populates='session', cascade='all, delete-orphan')
    tickets = relationship('Ticket', back_populates='session')

    __table_args__ = (
        Index('ix_sessions_user_lastmsg', 'user_id', last_message_at.desc()),
        Index('ix_sessions_status_lastmsg', 'status', last_message_at.desc()),
    )

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum('user', 'assistant', 'system'), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    session = relationship('Session', back_populates='messages')

    __table_args__ = (
        Index('ix_messages_session_id_created_at', 'session_id', 'created_at'),
    )