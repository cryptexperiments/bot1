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
    wallet_address = Column(String, nullable=True)
    tasks = relationship("UserTask", back_populates="user")

class UserTask(Base):
    __tablename__ = 'user_tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task = Column(Enum(Task))
    completed_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tasks")