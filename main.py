from users import ManagerFactory, ClientFactory, AdminFactory
from session import SessionManager
from reports import ReportBuilder, FinancialReportFactory
from order import ConcreteOrder, VolumeDiscount, VIPDiscount, InsuranceDecorator, PriorityShippingDecorator
from payment import StripeAPI, PayPalAPI, StripeAdapter, PayPalAdapter
from notification import OrderSubject, ClientObserver, ManagerObserver
from db import init_db, DbSessionManager, User
# ---- в начале main.py добавить ----
from db import init_db, DbSessionManager, User, Order
from getpass import getpass
import hashlib
from db import init_db, seed_admin, DbSessionManager, User, Order

# ---- в теле main.py ----

# инициализируем БД и создаём default admin
init_db()
seed_admin()

# ---- регистрация возвращает пользователя ----
def register():
    name = input("Имя: ")
    email = input("Email: ")
    pw = getpass("Пароль: ")
    with DbSessionManager() as db:
        if db.query(User).filter_by(email=email).first():
            print("Email занят")
            return None
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(pw),
            role=input("Роль (client/manager/admin): ") or "client"
        )
        db.add(user)
        db.commit()
        print("Зарегистрирован:", user.name, "(", user.role, ")")
        return user

# ---- login тоже возвращает пользователя ----
def login():
    email = input("Email: ")
    pw = getpass("Пароль: ")
    with DbSessionManager() as db:
        user = db.query(User).filter_by(email=email).first()
        if user and user.hashed_password == hash_password(pw):
            print(f"Добро пожаловать, {user.name} ({user.role})")
            return user
    print("Неверные учётные данные")
    return None

# ---- админ‑меню ----
def admin_menu(user):
    while True:
        print("\nAdmin: 1=Все пользователи, 2=Все заказы, 3=Выйти")
        cmd = input("Выберите: ")
        if cmd=='1':
            with DbSessionManager() as db:
                for u in db.query(User).all():
                    print(u.id, u.name, u.email, u.role)
        elif cmd=='2':
            with DbSessionManager() as db:
                for o in db.query(Order).all():
                    print(o.id, o.user_id, o.total, o.status, o.created_at)
        elif cmd=='3':
            break
        else:
            print("Неизвестная команда")

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def register():
    name = input("Имя: ")
    email = input("Email: ")
    pw = getpass("Пароль: ")
    with DbSessionManager() as db:
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(pw),
            role='client'
        )
        db.add(user)
        db.commit()
        print("Пользователь зарегистрирован, id=", user.id)


def login():
    email = input("Email: ")
    pw = getpass("Пароль: ")
    with DbSessionManager() as db:
        user = db.query(User).filter_by(email=email).first()
        if user and user.hashed_password == hash_password(pw):
            print(f"Добро пожаловать, {user.name} (роль: {user.role})")
        else:
            print("Неверные учётные данные")


# Простое меню регистрации/входа
if __name__ == "__main__":
    choice = input("1 = Register, 2 = Login: ")
    if choice == '1':
        register()
    else:
        login()
# Создание заказа в БД и применение паттернов декоратор/стратегия
def create_order(user):
    print("--- Создать заказ ---")
    with DbSessionManager() as db:
        # Простейший заказ: ввод суммы
        amount = int(input("Сумма заказа: "))
        # Вычисляем скидку через Strategy
        order_obj = ConcreteOrder(items=[{'price': amount}], is_vip=(user.role=="client" and False))
        # выбираем стратегию скидки
        strat = input("Стратегия скидки (none/volume/vip): ")
        if strat == "volume": order_obj.set_discount_strategy(VolumeDiscount())
        elif strat == "vip": order_obj.set_discount_strategy(VIPDiscount())
        # декораторы
        if input("Добавить страховку? (y/n): ") == 'y':
            order_obj = InsuranceDecorator(order_obj)
        if input("Добавить приоритетную доставку? (y/n): ") == 'y':
            order_obj = PriorityShippingDecorator(order_obj)
        total_price = order_obj.get_price()
        # сохраняем в БД
        order_record = Order(user_id=user.id, total=total_price)
        db.add(order_record)
        db.commit()
        print(f"✔ Заказ создан (id={order_record.id}), итоговая сумма: {total_price}")

# Показать заказы пользователя
def list_orders(user):
    print("--- Мои заказы ---")
    with DbSessionManager() as db:
        orders = db.query(Order).filter_by(user_id=user.id).all()
        if not orders:
            print("Нет заказов.")
        for o in orders:
            print(f"ID={o.id}, сумма={o.total}, статус={o.status}, дата={o.created_at}")

# Меню после входа
def user_menu(user):
    while True:
        print("\n1=Создать заказ, 2=Мои заказы, 3=Выйти")
        cmd = input("Выберите: ")
        if cmd == '1': create_order(user)
        elif cmd == '2': list_orders(user)
        elif cmd == '3': break
        else: print("Неизвестная команда.")

# Точка входа
if __name__ == "__main__":
    while True:
        print("\n1=Register, 2=Login, 3=Exit")
        choice = input("Выберите: ")
        if choice == '1':
            user = register()
            if user: user_menu(user)
        elif choice == '2':
            user = login()
            if user: user_menu(user)
        elif choice == '3':
            print("Выход.")
            break
        else:
            print("Неверный выбор.")


# 1. Пользователи и сессии
manager = ManagerFactory().create_user("Иван", "ivan@example.com")
client = ClientFactory().create_user("Пётр", "petr@example.com")
session = SessionManager()
session.login(manager)
session.login(client)

# 2. Отчёты
builder = ReportBuilder(FinancialReportFactory())
summary = builder.set_date_range("2025-01-01", "2025-05-01").add_filter("Регион=Молдова").build_summary()
print(summary.content)

# 3. Заказ
order = ConcreteOrder(items=[{'price': 600}, {'price': 700}], is_vip=True)
order.set_discount_strategy(VolumeDiscount())
print("Итог с учётом скидки:", order.get_price())

# 4. Декораторы услуг
decorated = InsuranceDecorator(order)
fully_decorated = PriorityShippingDecorator(decorated)
print("Итог с доп. услугами:", fully_decorated.get_price())

# 5. Платежи
stripe_proc = StripeAdapter(StripeAPI())
paypal_proc = PayPalAdapter(PayPalAPI())
stripe_proc.pay(500)
paypal_proc.pay(500)

# 6. Уведомления
order_subj = OrderSubject()
order_subj.attach(ClientObserver())
order_subj.attach(ManagerObserver())
order_subj.update_status("В обработке")
order_subj.update_status("Завершен")

if __name__ == "__main__":
    while True:
        print("\n1=Register, 2=Login, 3=Exit")
        choice = input("Выберите: ")
        if choice=='1':
            user = register()
        elif choice=='2':
            user = login()
        elif choice=='3':
            break
        else:
            print("Неверный выбор"); continue

        if user:
            if user.role=='admin':
                admin_menu(user)
            else:
                user_menu(user)