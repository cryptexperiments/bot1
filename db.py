from models import Base, User, UserTask, Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///bot.db')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def get_or_create_user(session, telegram_id):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, created_at=datetime.utcnow())
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
