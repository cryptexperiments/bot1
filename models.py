from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class Task(enum.Enum):
    FOLLOW_JIMMYBOSS_X = "follow_jimmyboss_x"
    FOLLOW_JBCOLLECTIVE_X = "follow_jbcollective_x"
    FOLLOW_JIMMYBOSS_CMC = "follow_jimmyboss_cmc"
    FOLLOW_JBC_TOKEN_CMC = "follow_jbc_token_cmc"
    SUBSCRIBE_YOUTUBE = "subscribe_youtube"
    JOIN_TELEGRAM_CHANNEL = "join_telegram_channel"
    JOIN_TELEGRAM_GROUP = "join_telegram_group"
    REFERRAL = "invite_friend"
    COMPLETED = "completed"

# Task instructions
task_instructions = {
    Task.FOLLOW_JIMMYBOSS_X: ("Follow JimmyBoss on X", "https://x.com/jimmyboss48"),
    Task.FOLLOW_JBCOLLECTIVE_X: ("Follow JBCollective on X", "https://x.com/JBCcollective"),
    Task.FOLLOW_JIMMYBOSS_CMC: ("Follow JimmyBoss on CoinMarketCap", "https://coinmarketcap.com/community/profile/Jimmyboss/"),
    Task.FOLLOW_JBC_TOKEN_CMC: ("Follow JBC Token on CoinMarketCap", "https://coinmarketcap.com/community/profile/JimmyBossCollective/"),
    Task.SUBSCRIBE_YOUTUBE: ("Subscribe to our YouTube Channel", "https://www.youtube.com/channel/UCDEUuvfe5bkFgpSvi143uwQ"),
    Task.JOIN_TELEGRAM_CHANNEL: ("Join our Telegram Channel", "https://t.me/JimmyBossCollective"),
    Task.JOIN_TELEGRAM_GROUP: ("Join our Telegram Group", "https://t.me/httpJBC_Official"),
    Task.REFERRAL: ("Invite at least one friend to join the bot", "/refer"),
    Task.COMPLETED: ("All tasks completed!", None),
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