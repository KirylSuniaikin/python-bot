import logging
import random
import uuid
import pytz
from datetime import datetime
from app.google_sheets import add_new_order, add_new_order_item, get_user_phone_number, update_user_info, user_exists, \
    add_new_user, get_active_orders, delete_order_info, edit_user_info, \
    menu_items_sheet, ger_photo_url_by_name_for_current_menu
from app.models.models import OrderTO, Order, OrderItem
from app.socketio import emit_order_created
from app.whatsapp import send_order_confirmation, send_info_to_kitchen, \
    send_order_to_kitchen_text2


def create_new_order(order: OrderTO, name):
    year_suffix = str(datetime.now(pytz.timezone("Asia/Bahrain")).year)[-2:]
    random_digits = str(random.randint(1000, 9999))
    order_no = f"a{year_suffix}{random_digits}"

    if order.tel:
        telephone_no = order.tel
        if not user_exists(telephone_no):
            add_new_user(telephone_no, name)
    else:
        telephone_no = get_user_phone_number(order.user_id) or "Unknown customer"

    address = ""
    order_items = order.items
    items = []

    sorted_items = sorted(order_items, key=lambda x: ["Combo Deals", "Brick Pizzas", "Pizzas", "Sides", "Sauces", "Beverages"].index(x["category"]))
    new_order = Order(
        order_no=order_no,
        telephone_no=telephone_no,
        status="Kitchen Phase",
        date_and_time=datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M"),
        type=order.type,
        address=address,
        amount_paid=order.amount_paid,
        payment_type=order.payment_type,
        notes=order.notes,
    )
    add_new_order(new_order)

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
            order_no=order_no,
            id=str(uuid.uuid4())[:8],
            name=item["name"],
            quantity=item["quantity"],
            amount=item["amount"],
            size=item.get("size", ""),
            category=category,
            isGarlicCrust=is_garlic_crust,
            isThinDough=is_thin_dough,
            description=description,
            sale_amount=discount_amount,
        )
        items.append(new_item)
        add_new_order_item(new_item)
    if telephone_no != "Unknown customer":
        update_user_info(new_order, name)
        send_order_confirmation(telephone_no, sorted_items, order.amount_paid, name)
    data = build_order_payload(new_order, items, name)
    emit_order_created(data)
    send_order_to_kitchen_text2(order_no, sorted_items, order.amount_paid, telephone_no, False)
    send_info_to_kitchen(order_no)

    return {
        "status": "success",
        "order_no": order_no,
        "message": "Order created successfully"
    }


def build_order_payload(order: Order, items: list[OrderItem], user_name: str) -> dict:
    menu = menu_items_sheet.get_all_records()
    return {
        "orderId": order.order_no,
        "order_type": order.type,
        "amount_paid": order.amount_paid,
        "phone_number": order.telephone_no,
        "sale_amount": round(sum(i.sale_amount or 0 for i in items), 2),
        "customer_name": user_name,
        "order_created": order.date_and_time,
        "payment_type": order.payment_type,
        "notes": order.notes,
        "items": [
            {
                "name": i.name,
                "quantity": i.quantity,
                "amount": i.amount,
                "size": i.size,
                "category": i.category,
                "isGarlicCrust": i.isGarlicCrust,
                "isThinDough": i.isThinDough,
                "description": i.description,
                "discount_amount": i.sale_amount,
                "photo": ger_photo_url_by_name_for_current_menu(i.name, menu),
            }
            for i in items
        ]
    }


def update_order(order: OrderTO, order_id: str):

    phone_no = edit_user_info(order, order_id)
    delete_order_info(order_id)

    address = ""
    order_items = order.items

    sorted_items = sorted(order_items, key=lambda x: ["Combo Deals", "Brick Pizzas", "Pizzas", "Sides", "Sauces", "Beverages"].index(x["category"]))

    new_order = Order(
        order_no=order_id,
        telephone_no=phone_no,
        status="Kitchen Phase",
        date_and_time=datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M"),
        type=order.type,
        address=address,
        amount_paid=order.amount_paid,
        payment_type=order.payment_type,
        notes=order.notes,
    )
    add_new_order(new_order)
    logging.info(f"New Items: {sorted_items}")
    for item in sorted_items:
        category = item["category"]
        description = item.get("description", "")
        is_garlic_crust = item.get("isGarlicCrust", False) if category in ["Pizzas", "Combo Deals"] else False
        is_thin_dough = item.get("isThinDough", False) if category in ["Pizzas", "Combo Deals"] else False

        new_item = OrderItem(
            order_no=order_id,
            id=str(uuid.uuid4())[:8],
            name=item["name"],
            quantity=item["quantity"],
            amount=item["amount"],
            size=item.get("size", ""),
            category=category,
            isGarlicCrust=is_garlic_crust,
            isThinDough=is_thin_dough,
            description=description,
            sale_amount=item["discount_amount"],
        )
        add_new_order_item(new_item)
    send_order_to_kitchen_text2(order_id, sorted_items, order.amount_paid, phone_no, True)

    # send_edit_order_confirmation(telephone_no, sorted_items, order.amount_paid, order_no)
    # send_edit_order_to_kitchen_text2(order_no, sorted_items, order.amount_paid, telephone_no)
    # send_edit_info_to_kitchen(order_no)


def get_all_active_orders(): return get_active_orders()