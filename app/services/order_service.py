import logging
import random
import threading
import pytz
from datetime import datetime
from app.models.models import OrderTO, Order, OrderItem
from app.repositories.repository import is_user_exist, add_new_user, create_order, create_new_items, update_customer, \
    get_customer_by_id, get_active_orders, update_order_transaction
from app.socketio import emit_order_created, emit
from app.whatsapp import send_order_confirmation, send_order_to_kitchen_text2, build_kitchen_message, send_ready_message
from flask import current_app


def create_new_order(order: OrderTO, name):
    telephone_no = None
    if order.tel:
        telephone_no = order.tel
        if not is_user_exist(telephone_no):
            add_new_user(telephone_no, name)
    else:
        customer = get_customer_by_id(order.user_id)
        if customer:
            telephone_no = customer.telephone_no
            name = customer.name

    address = ""
    order_items = order.items
    items = []

    sorted_items = sorted(order_items, key=lambda x: ["Combo Deals", "Brick Pizzas", "Pizzas", "Sides", "Sauces", "Beverages"].index(x["category"]))
    new_order = Order(
        id=random.randint(1, 99999999),
        order_no=random.randint(1, 999),
        telephone_no=telephone_no,
        status="Kitchen Phase",
        created_at=datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M"),
        type=order.type,
        amount_paid=order.amount_paid,
        payment_type=order.payment_type,
        notes=order.notes,
        address=address
    )
    create_order(new_order)

    for item in sorted_items:
        discount_raw = item.get("discount_amount", 0.0)
        try:
            discount_amount = discount_raw
        except (ValueError, TypeError):
            discount_amount = 0.0
        category = item["category"]
        description = item.get("description", "")
        is_garlic_crust = item.get("isGarlicCrust", False) if category in ["Pizzas", "Combo Deals"] else False
        is_thin_dough = item.get("isThinDough", False) if category in ["Pizzas", "Combo Deals"] else False
        new_item = OrderItem(
            order_id=new_order.id,
            id=random.randint(1, 99999999),
            name=item["name"],
            quantity=item["quantity"],
            amount=item["amount"],
            size=item.get("size", ""),
            category=category,
            is_garlic_crust=is_garlic_crust,
            is_thin_dough=is_thin_dough,
            description=description,
            discount_amount=discount_amount,
        )
        items.append(new_item)
    dict_items = create_new_items(items)
    appctx = current_app.app_context()
    threading.Thread(target=async_new_order_post_processing, args=(appctx, new_order, new_order.telephone_no, dict_items, name)).start()

    return {
        "status": "success",
        "order_no": new_order.id,
        "message": "Order created successfully"
    }

def async_new_order_post_processing(appctx, order, telephone_no, sorted_items, name):
    with appctx:
        message_body = build_kitchen_message(sorted_items)
        if telephone_no and telephone_no != "Unknown customer":
            update_customer(order)
            send_order_confirmation(telephone_no, message_body, order.amount_paid, order.id)
        data = build_order_payload(order, sorted_items, name)
        print("we are here")
        emit_order_created(data)
        send_order_to_kitchen_text2(order.order_no, message_body, telephone_no, False, name)
        # send_info_to_kitchen(order.order_no)

def async_ready_order_post_processing(appctx, order):
    with appctx:
        send_ready_message(order.telephone_no, order.customer.name, order.customer.id)

def build_order_payload(order: Order, items: list, user_name: str) -> dict:
    return {
        "orderId": order.order_no,
        "order_type": order.type,
        "amount_paid": order.amount_paid,
        "phone_number": order.telephone_no,
        "discount_amount": round(sum(i.get("discount_amount", 0.0) or 0.0 for i in items), 2),
        "customer_name": user_name,
        "order_created": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "payment_type": order.payment_type,
        "notes": order.notes,
        "items": [
            {
                "name": i["name"],
                "quantity": i["quantity"],
                "amount": i["amount"],
                "size": i.get("size", ""),
                "category": i.get("category", ""),
                "is_garlic_crust": i.get("is_garlic_crust", False),
                "is_thin_dough": i.get("is_thin_dough", False),
                "description": i.get("description", ""),
                "discount_amount": i.get("discount_amount", 0.0),
                "photo": i.get("photo", ""),
            }
            for i in items
        ]
    }


def update_order(order: OrderTO):
    order_info = update_order_transaction(order)
    print("lol22")
    if not order_info:
        logging.warning("Order update failed; skipping post-processing.")
        return
    if order.tel and order.tel != "Unknown customer":
        print("lol")
        sorted_items = order_info.get("sorted_items", [])
        customer_name = order_info.get("customer_name", "no name")

        appctx = current_app.app_context()
        threading.Thread(target=async_update_order_post_processing, args=(appctx, order, sorted_items, customer_name)).start()


def async_update_order_post_processing(appctx, order: OrderTO, sorted_items, customer_name):
    with appctx:
        message_body = build_kitchen_message(sorted_items)
        send_order_to_kitchen_text2(order.id, message_body, order.tel, True, customer_name)


def get_all_active_orders():
    orders = get_active_orders()

    active_orders = []
    for order in orders:
        customer_name = order.customer.name if order.customer and order.customer.name else None

        items = []
        print(order.items)
        for item in order.items:
            items.append({
                "name": item.name,
                "quantity": item.quantity,
                "amount": item.amount,
                "size": item.size,
                "category": item.category,
                "isGarlicCrust": item.is_garlic_crust,
                "isThinDough": item.is_thin_dough,
                "description": item.description,
                "discount_amount": item.discount_amount or 0,
                "photo": next((m["photo"] for m in current_app.menu_cache if m["name"] == item.name), "")
            })

        active_orders.append({
            "id": order.id,
            "order_no": order.order_no,
            "order_type": order.type,
            "amount_paid": order.amount_paid,
            "phone_number": order.telephone_no,
            "address": order.address,
            "sale_amount": round(sum(i["discount_amount"] for i in items), 2),
            "customer_name": customer_name,
            "order_created": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "",
            "payment_type": order.payment_type,
            "notes": order.notes or "",
            "items": items
        })

    return {"orders": active_orders}
