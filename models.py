from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    upi_id = Column(String, nullable=True)


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Integer, default=0)


class Ledger(Base):
    __tablename__ = "ledger"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, nullable=True)
    to_user_id = Column(Integer)
    amount = Column(Integer)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class TipRequest(Base):
    __tablename__ = "tip_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
