import random
from datetime import datetime, timedelta, time
import logging
import pytz
from flask import current_app
from sqlalchemy import func, distinct, cast, Numeric, text
from app.conf.db_conf import db
from app.models.models import Order, OrderItem, Customer, MenuItem, OrderTO, ExtraIngr, Event

BAHRAIN_TZ = pytz.timezone("Asia/Bahrain")

##########
#ORDERS
##########

def get_unique_customers_all_time_in_orders():
    return db.session.query(func.count(distinct(Order.telephone_no))).filter(Order.telephone_no != None).scalar() or 0


def create_order(order: Order):
    db.session.add(order)
    db.session.commit()

def update_payment(id, type):
    Order.query.filter_by(id=id).update({'payment_type': type})
    db.session.commit()

def get_active_orders():
    query = (
        db.session.query(Order)
        .filter(Order.status != "Ready")
        .options(
            db.joinedload(Order.items),
            db.joinedload(Order.customer)
        )
    )
    return query.all()


def update_order_transaction(order: OrderTO):
    with db.session.begin():
        # Step 1: Get old order
        old_order = Order.query.filter_by(id=order.id).first()
        if not old_order:
            logging.warning(f"Order with ID {order.id} not found.")
            return

        old_amount_paid = old_order.amount_paid

        customer = None
        if order.tel:
            # Step 2: Update customer
            customer = Customer.query.filter_by(telephone_no=old_order.telephone_no).first()
            if not customer:
                logging.warning(f"User with phone {old_order.telephone_no} not found.")
                return

            customer.amount_paid = customer.amount_paid - old_amount_paid + order.amount_paid
            customer.last_order = datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M")

            logging.info(f"User {customer.telephone_no} updated after order edit. Old paid: {old_amount_paid}, New paid: {order.amount_paid}, Total: {customer.amount_paid}")

        # Step 3: Update order fields
        old_order.address = order.address
        old_order.amount_paid = order.amount_paid
        old_order.payment_type = order.payment_type
        old_order.notes = order.notes

        # Step 4: Delete old items
        OrderItem.query.filter_by(order_id=old_order.id).delete()

        # Step 5: Add new items
        items = []
        sorted_items = sorted(order.items, key=lambda x: ["Combo Deals", "Brick Pizzas", "Pizzas", "Sides", "Sauces", "Beverages"].index(x["category"]))

        for item in sorted_items:
            category = item["category"]
            description = item.get("description", "")
            is_garlic_crust = item.get("isGarlicCrust", False) if category in ["Pizzas", "Combo Deals"] else False
            is_thin_dough = item.get("isThinDough", False) if category in ["Pizzas", "Combo Deals"] else False

            new_item = OrderItem(
                order_id=old_order.id,
                id=random.randint(1, 99999999),
                name=item["name"],
                quantity=item["quantity"],
                amount=item["amount"],
                size=item.get("size", ""),
                category=category,
                is_garlic_crust=is_garlic_crust,
                is_thin_dough=is_thin_dough,
                description=description,
                discount_amount=item.get("discount_amount", 0.0),
            )
            items.append(new_item)

        db.session.add_all(items)

        logging.info(f"Order {old_order.id} updated successfully with new items.")
    return {
        "sorted_items": sorted_items,
        "customer_name": customer.name if customer else None
    }

def get_history_orders():
    bahrain_tz = pytz.timezone("Asia/Bahrain")
    now = datetime.now(bahrain_tz)
    cutoff_time = now - timedelta(days=1)

    orders = (
        Order.query
        .filter(Order.status == "Ready", Order.created_at >= cutoff_time)
        .all()
    )

    history_orders = []
    for order in orders:
        items = []
        for item in order.items:
            try:
                items.append({
                    "name": item.name,
                    "quantity": item.quantity,
                    "amount": item.amount,
                    "size": item.size,
                    "category": item.category,
                    "isGarlicCrust": item.is_garlic_crust,
                    "isThinDough": item.is_thin_dough,
                    "description": item.description,
                    "discount_amount": item.discount_amount,
                    "photo": next((m["photo"] for m in current_app.menu_cache if m["name"] == item.name), ""),
                })
            except Exception as e:
                print(f"Ошибка при обработке item: {item.name}, {e}")

        history_orders.append({
            "id": order.id,
            "order_no": order.order_no,
            "order_type": order.type,
            "amount_paid": order.amount_paid,
            "phone_number": order.telephone_no,
            "sale_amount": round(sum(i["discount_amount"] or 0 for i in items), 2),
            "customer_name": order.customer.name if order.customer and order.customer.name else "Unknown customer",
            "order_created": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "",
            "payment_type": order.payment_type,
            "notes": order.notes or "",
            "items": items
        })

    logging.info(history_orders)
    return {"orders": history_orders}


def get_orders_with_customers_for_period(start_date, finish_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    finish_date = datetime.strptime(finish_date, "%Y-%m-%d")

    start_datetime = start_date + timedelta(hours=2)
    finish_datetime = finish_date + timedelta(days=1, hours=1, minutes=59, seconds=59)
    print(start_datetime)
    print(finish_datetime)

    return db.session.query(
        Order,
        Customer.amount_of_orders
    ).outerjoin(
        Customer,
        Customer.telephone_no == Order.telephone_no
    ).filter(
        Order.created_at >= start_datetime,
        Order.created_at <= finish_datetime
    ).all()


def make_order_ready(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        logging.error(f"Order {order_id} not found")
        return

    order.status = "Ready"
    db.session.commit()
    return order


##########
#ORDER_ITEMS
##########

def create_new_items(items: [OrderItem]):
    db.session.add_all(items)
    db.session.commit()
    item_dicts = []
    for item in items:
        item_dicts.append({
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "amount": item.amount,
            "size": item.size,
            "category": item.category,
            "is_garlic_crust": item.is_garlic_crust,
            "is_thin_dough": item.is_thin_dough,
            "description": item.description,
            "discount_amount": item.discount_amount,
        })

    return item_dicts



##########
#MENU_ITEMS
##########

def get_menu_items():
    return MenuItem.query.all()

def update_menu_tems_availability(name, enabled):
    MenuItem.query.filter_by(name=name).update({'available': enabled})
    db.session.commit()

def update_dough_availability(size, enabled):
    MenuItem.query.filter_by(size=size).update({'available': enabled})
    db.session.commit()

def update_brick_pizza_availability(enabled):
    MenuItem.query.filter_by(category="Brick Pizzas").update({'available': enabled})
    db.session.commit()


##########
#MENU_ITEMS
##########

def get_extra_ingr():
    return ExtraIngr.query.all()



##########
#CUSTOMERS
##########

def update_customer(order):
    customer = Customer.query.filter_by(telephone_no=order.telephone_no).first()

    if not customer:
        print(f"User with phone {order.telephone_no} not found")
        return

    customer.amount_of_orders += 1
    customer.amount_paid += order.amount_paid
    customer.amount_paid = round(customer.amount_paid, 3)
    customer.last_order = datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M")

    db.session.commit()

    print(f"User {order.telephone_no} updated: orders={customer.amount_of_orders}, paid={customer.amount_paid}, last_order={customer.last_order}")


def is_user_exist(tel):
    return db.session.query(Customer.id).filter_by(telephone_no=tel).first() is not None


def add_new_user(telephone_no, name):
    new_customer = Customer(
        id=random.randint(1, 99999999),
        telephone_no=telephone_no,
        name=name,
        address="",
        amount_of_orders=0,
        amount_paid=0.0,
        last_order=None,
        waiting_for_name=None
    )
    db.session.add(new_customer)
    db.session.commit()


def get_customer_by_id(user_id):
    return Customer.query.filter_by(id=user_id).first()

def get_user_id(phone_number):
    customer = Customer.query.filter_by(telephone_no=phone_number).first()
    if customer:
        return customer.id
    return None

def set_wait_for_name(phone_number, status):
    customer = Customer.query.filter_by(telephone_no=phone_number).first()
    if customer:
        customer.waiting_for_name = int(status)
        db.session.commit()

def is_wait_for_name(phone_number):
    customer = Customer.query.filter_by(telephone_no=phone_number).first()
    if customer:
        is_waiting = customer.waiting_for_name == 1
        return is_waiting
    return False

def save_user_name(phone_number, name):
    customer = Customer.query.filter_by(telephone_no=phone_number).first()
    if customer:
        customer.name = name
        db.session.commit()

def user_exists(phone_number):
    return Customer.query.filter_by(telephone_no=phone_number).first() is not None

def user_has_name(phone_number):
    customer = Customer.query.filter_by(telephone_no=phone_number).first()
    if customer:
        has_name = bool(customer.name and customer.name.strip())
        return has_name
    return False


def get_user_info(user_id):
    customer = Customer.query.filter_by(id=user_id).first()
    if customer:
        return {
            "phone": customer.telephone_no,
            "name": customer.name
        }
    return {
        "phone": None,
        "name": None
    }


def get_customer_stats():
    result = db.session.query(
        func.count(distinct(Customer.telephone_no)).label("unique_customers"),
        func.count().filter(Customer.amount_of_orders > 1).label("repeat_customers")
    ).one()

    return {
        "unique_customers_all_time": result.unique_customers,
        "repeat_customers_all_time": result.repeat_customers
    }


def get_arpu_aov():
    result = db.session.query(
        func.round(
            cast(func.sum(Customer.amount_paid), Numeric) / func.count(distinct(Customer.telephone_no)), 2
        ).label("ARPU"),
        func.round(
            cast(func.sum(Customer.amount_paid), Numeric) / func.sum(Customer.amount_of_orders), 2
        ).label("AOV")
    ).one()

    return {
        "ARPU": float(result.ARPU),
        "AOV": float(result.AOV)
    }


def get_retention_metric(certain_date):
    certain_dt = datetime.strptime(certain_date, "%Y-%m-%d")
    prev_month_start = (certain_dt.replace(day=1) - timedelta(days=1)).replace(day=1)
    curr_month_start = certain_dt.replace(day=1)
    curr_date_end = certain_dt

    print("prev_month_start:", prev_month_start.strftime("%Y-%m-%d"))
    print("end:", curr_month_start.strftime("%Y-%m-%d"))

    first_orders_subq = (
        db.session.query(
            Order.telephone_no.label("tel"),
            func.min(Order.created_at).label("first_order_date")
        ).group_by(Order.telephone_no)
    ).subquery()

    prev_month_customers = (
        db.session.query(first_orders_subq.c.tel)
        .filter(
            first_orders_subq.c.first_order_date >= prev_month_start,
            first_orders_subq.c.first_order_date < curr_month_start
        )
    ).subquery()

    month_total_customers = db.session.query(prev_month_customers).count()

    retained_customers = db.session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT DISTINCT o.telephone_no
            FROM orders o
            JOIN (
                SELECT telephone_no, MIN(created_at) AS first_order
                FROM orders
                GROUP BY telephone_no
                HAVING MIN(created_at) >= :prev_month_start AND MIN(created_at) < :curr_month_start
            ) first_orders
            ON o.telephone_no = first_orders.telephone_no
            WHERE o.created_at > first_orders.first_order
              AND o.created_at <= :curr_date_end
        ) retained
    """), {
        "prev_month_start": prev_month_start,
        "curr_month_start": curr_month_start,
        "curr_date_end": curr_date_end
    }).scalar()

    retention_percentage = (retained_customers / month_total_customers * 100) if month_total_customers else 0

    return {
        "month_total_customers": month_total_customers,
        "retained_customers": retained_customers,
        "retention_percentage": retention_percentage
    }

##########
#SHIFT
##########

def get_latest_stage(branch_id):
    event = (
        Event.query
        .filter_by(branch_id=branch_id)
        .order_by(Event.datetime.desc())
        .first()
    )
    logging.info(f"latest_stage: {event}")
    return event.type.value if event else None

def get_open_shift_cash(branch_id):
    bahrain_tz = pytz.timezone("Asia/Bahrain")
    now = datetime.now(bahrain_tz)
    today = now.date()

    if now.time() < time(2, 0):
        shift_start_date = today - timedelta(days=1)
    else:
        shift_start_date = today

    shift_end_date = shift_start_date + timedelta(days=1)

    start_time = datetime.combine(shift_start_date, time(14, 0))
    end_time = datetime.combine(shift_end_date, time(2, 0))

    logging.info(f"[CASH CHECK] Time range (Bahrain local): {start_time} to {end_time}")

    event = db.session.query(Event).filter(
        Event.type == 'OPEN_SHIFT_CASH_CHECK',
        Event.branch_id == branch_id,
        Event.datetime >= start_time,
        Event.datetime < end_time
    ).order_by(Event.datetime.desc()).first()

    if event:
        logging.info(f"[CASH CHECK] ✅ Found OPEN_SHIFT_CASH_CHECK: {event.cash_amount}")
        return event.cash_amount
    return 0.0



def get_total_cash_orders():
    bahrain_tz = pytz.timezone("Asia/Bahrain")
    now = datetime.now(bahrain_tz)
    today = now.date()

    if now.time() < time(2, 0):
        shift_start_date = today - timedelta(days=1)
    else:
        shift_start_date = today

    shift_end_date = shift_start_date + timedelta(days=1)

    start_time = datetime.combine(shift_start_date, time(14, 0))
    end_time = datetime.combine(shift_end_date, time(2, 0))

    cash_orders = db.session.query(Order).filter(
        Order.payment_type == 'Cash',
        Order.created_at >= start_time,
        Order.created_at < end_time
    ).all()

    total_cash = sum(order.amount_paid for order in cash_orders)

    return total_cash

