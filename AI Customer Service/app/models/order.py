from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, DECIMAL, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    items = Column(JSON, nullable=False)  # 商品列表，例如 [{"name": "商品A", "quantity": 2, "price": 99.99}]
    total_amount = Column(DECIMAL(10,2), nullable=False)
    status = Column(Enum('pending','paid','shipped','completed','cancelled'), default='pending')
    receiver_name = Column(String(100), nullable=False)
    receiver_phone = Column(String(20), nullable=False)
    shipping_address = Column(Text, nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='orders')
    tickets = relationship('Ticket', back_populates='order')

    __table_args__ = (
        Index('ix_orders_user_id', 'user_id'),
        Index('ix_orders_status_created', 'status', created_at.desc()),
    )