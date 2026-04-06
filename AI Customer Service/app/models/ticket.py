from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(50), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    session_id = Column(Integer, ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True)
    type = Column(Enum('complaint','return','exchange','other'), nullable=False)
    title = Column(String(200))
    description = Column(Text, nullable=False)
    status = Column(Enum('open','processing','closed'), default='open')
    assigned_to = Column(String(50))
    resolution = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='tickets')
    order = relationship('Order', back_populates='tickets')
    session = relationship('Session', back_populates='tickets')

    __table_args__ = (
        Index('ix_tickets_user_id', 'user_id'),
        Index('ix_tickets_order_id', 'order_id'),
        Index('ix_tickets_session_id', 'session_id'),
        Index('ix_tickets_status_created', 'status', created_at.desc()),
    )