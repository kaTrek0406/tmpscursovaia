# main.py

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, make_response, flash
)
import hashlib
from datetime import datetime
import io, csv

from db import init_db, seed_admin, DbSessionManager, User, Order as OrderModel
from order import (
    ConcreteOrder, VolumeDiscount, VIPDiscount,
    InsuranceDecorator, PriorityShippingDecorator
)
from payment import StripeAdapter, PayPalAdapter, StripeAPI, PayPalAPI
from notification import OrderSubject, ClientObserver, ManagerObserver
from reports import (
    ReportBuilder,
    FinancialReportFactory, AnalyticalReportFactory, LogisticsReportFactory
)

from users import ManagerFactory, ClientFactory, AdminFactory
from sqlalchemy import func
from flask import jsonify
from db import log_audit
from db import Audit


app = Flask(__name__)
app.secret_key = 'change_this_secret'

# Инициализация БД и создание default admin
init_db()
seed_admin()

# утилита хеширования

@app.route('/api/sales_data')
def sales_data():
    # Только авторизованный
    if 'user_id' not in session:
        return jsonify([]), 401

    # Группируем заказы по дате (день) и суммируем total
    with DbSessionManager() as db:
        rows = (
            db.query(
                func.date(OrderModel.created_at).label('date'),
                func.sum(OrderModel.total).label('sum')
            )
            .group_by(func.date(OrderModel.created_at))
            .order_by(func.date(OrderModel.created_at))
            .all()
        )

    # Преобразуем в списки
    data = {
        'labels': [row.date.strftime('%Y-%m-%d') for row in rows],
        'totals': [float(row.sum) for row in rows]
    }
    return jsonify(data)


@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    # Только авторизованный пользователь
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_status = request.form.get('status')
    if new_status not in ('Создан', 'В обработке', 'Отправлен', 'Завершен'):
        flash('Недопустимый статус', 'danger')
        return redirect(url_for('orders'))

    # Обновляем в БД
    with DbSessionManager() as db:
        order = db.query(OrderModel).get(order_id)
        if not order:
            flash('Заказ не найден', 'danger')
            return redirect(url_for('orders'))
        order.status = new_status
        db.commit()
        log_audit('Order', order_id, 'status_change', detail=new_status, performed_by=session['user_id'])
    # Observer: уведомляем о новой верси статуса
    subj = OrderSubject()
    subj.attach(ClientObserver())
    subj.attach(ManagerObserver())
    subj.update_status(new_status)

    flash(f'Статус заказа {order_id} обновлён на «{new_status}»', 'success')
    return redirect(url_for('orders'))


@app.route('/admin/create_user', methods=['GET','POST'])
def admin_create_user():
    if 'user_id' not in session or session.get('user_role')!='admin':
        return redirect(url_for('login'))

    error = None
    if request.method=='POST':
        name  = request.form['name']
        email = request.form['email']
        pw    = request.form['password']
        role  = request.form['role']

        with DbSessionManager() as db:
            if db.query(User).filter_by(email=email).first():
                error = 'Email уже занят'
            else:
                # 1) создаём «бизнес‑объект» через Factory Method
                if role=='manager':
                    biz = ManagerFactory().create_user(name, email)
                elif role=='admin':
                    biz = AdminFactory().create_user(name, email)
                else:
                    biz = ClientFactory().create_user(name, email)

                # 2) конвертируем его в ORM‑модель и сохраняем
                orm_user = User(
                    name=biz.name,
                    email=biz.email,
                    hashed_password=hash_password(pw),
                    role=biz.role()
                )
                db.add(orm_user)
                db.commit()
                from db import log_audit
                log_audit('User', orm_user.id, 'create', detail=f"role={orm_user.role()}",
                          performed_by=session['user_id'])

                return redirect(url_for('admin_panel'))

    return render_template('admin_create_user.html', error=error)


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# --- Маршруты ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pw = request.form['password']
        with DbSessionManager() as db:
            if db.query(User).filter_by(email=email).first():
                return render_template('register.html', error='Email занят')
            user = User(name=name, email=email, hashed_password=hash_password(pw), role='client')
            db.add(user)
            db.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pw = request.form['password']
        with DbSessionManager() as db:
            user = db.query(User).filter_by(email=email).first()
            if user and user.hashed_password == hash_password(pw):
                session['user_id'] = user.id
                session['user_role'] = user.role
                return redirect(url_for('dashboard'))
        return render_template('login.html', error='Неверные данные')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with DbSessionManager() as db:
        orders = db.query(OrderModel).filter_by(user_id=session['user_id']).all()
    return render_template('orders.html', orders=orders)

@app.route('/create_order', methods=['GET','POST'])
def create_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        amt = int(request.form['amount'])
        strat = request.form['strategy']
        order_obj = ConcreteOrder(items=[{'price': amt}], is_vip=False)
        if strat == 'volume':
            order_obj.set_discount_strategy(VolumeDiscount())
        elif strat == 'vip':
            order_obj.set_discount_strategy(VIPDiscount())
        if request.form.get('insurance') == 'on':
            order_obj = InsuranceDecorator(order_obj)
        if request.form.get('priority') == 'on':
            order_obj = PriorityShippingDecorator(order_obj)
        total = order_obj.get_price()
        with DbSessionManager() as db:
            rec = OrderModel(user_id=session['user_id'], total=total, created_at=datetime.now())
            db.add(rec)
            db.commit()
            log_audit('Order', rec.id, 'create', detail=f"total={rec.total}", performed_by=session['user_id'])
        return redirect(url_for('orders'))
    return render_template('create_order.html')

from reports import ReportBuilder, FinancialReportFactory, AnalyticalReportFactory, LogisticsReportFactory

# … ваши прежние импорты и маршруты …

@app.route('/reports', methods=['GET','POST'])
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    report_types = {
        'financial': 'Финансовый',
        'analytical': 'Аналитический',
        'logistics': 'Логистический'
    }
    result = None

    if request.method == 'POST':
        rtype = request.form['type']
        start = request.form['start_date']
        end   = request.form['end_date']
        filt  = request.form.get('filter')

        # выбираем нужную фабрику
        if rtype == 'financial':
            factory = FinancialReportFactory()
        elif rtype == 'analytical':
            factory = AnalyticalReportFactory()
        else:
            factory = LogisticsReportFactory()

        # строим отчёт через Builder
        builder = ReportBuilder(factory)
        builder.set_date_range(start, end)
        if filt:
            builder.add_filter(filt)

        summary  = builder.build_summary().content
        detailed = builder.build_detailed().content
        result = {'summary': summary, 'detailed': detailed}

    return render_template('reports.html',
                           report_types=report_types,
                           result=result)

@app.route('/export_reports')
def export_reports():
    # забираем все заказы и связанных пользователей
    with DbSessionManager() as db:
        orders = db.query(OrderModel).all()
        users = {u.id: u for u in db.query(User).all()}

    # формируем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Order ID','User','Role','Total','Status','Created At'])
    for o in orders:
        u = users.get(o.user_id)
        writer.writerow([
            o.id,
            u.name if u else '',
            u.role if u else '',
            o.total,
            o.status,
            o.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    # отдаем файл
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=reports.csv'
    response.mimetype = 'text/csv'
    return response

# Adapter: единый маршрут оплаты
@app.route('/pay/<int:order_id>/<provider>')
def pay_order(order_id, provider):
    with DbSessionManager() as db:
        order = db.query(OrderModel).get(order_id)
    if not order:
        flash("Заказ не найден", "danger")
        return redirect(url_for('orders'))

    # Собираем паттерн Adapter
    if provider == 'stripe':
        proc = StripeAdapter(StripeAPI())
    else:
        proc = PayPalAdapter(PayPalAPI())
    proc.pay(order.total)
    flash(f"Заказ {order_id} оплачен через {provider}", "success")
    return redirect(url_for('orders'))

# Prototype: клонировать заказ в БД
@app.route('/clone/<int:order_id>')
def clone_order(order_id):
    with DbSessionManager() as db:
        orig = db.query(OrderModel).get(order_id)
        if not orig:
            flash("Заказ не найден", "danger")
            return redirect(url_for('orders'))
        clone = OrderModel(
            user_id=orig.user_id,
            total=orig.total,
            status='Cloned',
            created_at=datetime.now()
        )
        db.add(clone)
        db.commit()
    flash(f"Заказ {order_id} клонирован как {clone.id}", "info")
    return redirect(url_for('orders'))

# Observer: разослать уведомления по статусу
from notification import OrderSubject, ClientObserver, ManagerObserver
@app.route('/notify/<int:order_id>')
def notify_order(order_id):
    # Здесь мы просто демонстрируем паттерн — уведомляем клиентов и менеджеров
    subj = OrderSubject()
    subj.attach(ClientObserver())
    subj.attach(ManagerObserver())
    subj.update_status(f"Notification for order {order_id}")
    flash(f"Уведомления по заказу {order_id} отправлены", "warning")
    return redirect(url_for('orders'))

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_role') != 'admin':
        return "Доступ запрещён", 403

    with DbSessionManager() as db:
        users  = db.query(User).all()
        orders = db.query(OrderModel).all()
        audit  = db.query(Audit).order_by(Audit.timestamp.desc()).all()

    return render_template('admin.html',
                           users=users,
                           orders=orders,
                           audit=audit)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
