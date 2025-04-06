from models import Base, User, UserTask, Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///bot.db')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def get_or_create_user(session, telegram_id, referral_code=None):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, created_at=datetime.utcnow(), referral_code=referral_code)
        if referral_code:
            referred_by = session.query(User).filter_by(referral_code=referral_code).first()
            if referred_by:
                user.referred_by = referred_by.referral_code
                referred_by.referral_count += 1
                session.add(referred_by)
        session.add(user)
        session.commit()
    return user

def add_task(session, user, task):
    exists = session.query(UserTask).filter_by(user_id=user.id, task=task).first()
    if not exists:
        session.add(UserTask(user_id=user.id, task=task, completed_at=datetime.utcnow()))
        session.commit()

def get_user_tasks(session, user):
    return [t.task for t in user.tasks]

def set_wallet(session, user, wallet_address):
    if wallet_address:
        user.wallet_address = wallet_address
        session.commit()
        return True
    return False
