from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class Task(enum.Enum):
    STARTED = "started"
    STATUS = "status"
    WALLET_ADDED = "wallet_added"
    REFERRAL_DONE = "referral_done"
    COMPLETED = "completed"

task_instructions = {
    Task.STARTED: ("Start the bot", "/start"),
    Task.STATUS: ("Review your account", "/status"),
    Task.WALLET_ADDED: ("Add your wallet address", "/add_wallet <your_wallet_here>"),
    Task.REFERRAL_DONE: ("Invite at least one friend", "/refer"),
    Task.COMPLETED: ("All done!", None),
}

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    wallet_at = Column(DateTime, default=datetime.utcnow)
    wallet_address = Column(String, nullable=True)
    referral_code = Column(String, nullable=True)
    referred_by = Column(String, nullable=True)
    tasks = relationship("UserTask", back_populates="user")
    referral_count = Column(Integer, default=0)
    referral_at = Column(DateTime, default=datetime.utcnow)
    all_tasks_completed = Column(Integer, default=0)
    all_tasks_completed_at = Column(DateTime, default=datetime.utcnow)

class UserTask(Base):
    __tablename__ = 'user_tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task = Column(Enum(Task))
    completed_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tasks")
    
class Referral(Base):
    __tablename__ = 'referrals'
    id = Column(Integer, primary_key=True)
    referred_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # The user who referred
    referred_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # The user who was referred
    referred_at = Column(DateTime, default=datetime.utcnow)  # Timestamp of the referral

    referred_by = relationship("User", foreign_keys=[referred_by_id], backref="referrals_made")
    referred_user = relationship("User", foreign_keys=[referred_user_id], backref="referrals_received")