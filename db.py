"""
Модуль db.py: настройка SQLAlchemy и ORM-моделей для полноценной CRM
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from sqlalchemy.exc import IntegrityError
import hashlib
# 1) Настройка подключения к SQLite
DATABASE_URL = "sqlite:///crm.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def seed_admin():
    db = SessionLocal()
    try:
        admin = User(
            name="Администратор",
            email="admin",                   # т. к. поле теперь type="text"
            hashed_password=hashlib.sha256("admin".encode()).hexdigest(),
            role="admin"
        )
        db.add(admin)
        db.commit()
        print("✔ Создан default admin/admin")
    except IntegrityError:
        db.rollback()
    finally:
        db.close()

# 2) Модель пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 3) Модель заказа
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total = Column(Integer, nullable=False)
    status = Column(String, default='Создан')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="orders")

User.orders = relationship("Order", order_by=Order.id, back_populates="user")

class Audit(Base):
    __tablename__ = 'audit'
    id         = Column(Integer, primary_key=True, index=True)
    entity     = Column(String, nullable=False)   # 'User' или 'Order'
    entity_id  = Column(Integer, nullable=True)   # id пользователя или заказа
    action     = Column(String, nullable=False)   # 'create','status_change' и т.п.
    detail     = Column(String, nullable=True)    # доп. информация, например новый статус
    performed_by = Column(Integer, nullable=True) # user_id, кто сделал
    timestamp  = Column(DateTime, default=datetime.datetime.now)

def log_audit(entity, entity_id, action, detail=None, performed_by=None):
    db = SessionLocal()
    try:
        entry = Audit(
          entity=entity,
          entity_id=entity_id,
          action=action,
          detail=detail,
          performed_by=performed_by
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


# 4) Функция инициализации базы (создаёт таблицы)
def init_db():
    Base.metadata.create_all(bind=engine)

# 5) Утилиты для работы с сессиями БД
class DbSessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

# Пример инициализации при первом запуске
if __name__ == '__main__':
    init_db()
    Base.metadata.create_all(bind=engine)  # чтобы создалась таблица audit
    print("База данных и таблицы созданы")
