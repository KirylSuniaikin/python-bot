import logging
import uuid
from datetime import datetime

from app.google_sheets import add_new_order, add_new_order_item, get_user_phone_number, update_user_info, user_exists, \
    add_new_user
from app.models.models import OrderTO, Order, OrderItem
from app.whatsapp import send_order_confirmation


def create_new_order(order: OrderTO):
    order_no = str(uuid.uuid4())[:8]

    if order.tel:
        telephone_no = order.tel
        if not user_exists(telephone_no):
            add_new_user(telephone_no)
    else:
        telephone_no = get_user_phone_number(order.user_id) or "Error: unknown customer"

    address = ""
    order_items = order.items

    sorted_items = sorted(order_items, key=lambda x: ["Combo Deals", "Pizzas", "Sides", "Beverages"].index(x["category"]))
    logging.info(order)

    new_order = Order(
        order_no=order_no,
        telephone_no=telephone_no,
        status="Kitchen Phase",
        date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        type="Pickup",
        address=address,
        amount_paid=order.amount_paid
    )
    add_new_order(new_order)

    for item in sorted_items:
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
            description=description
        )
        add_new_order_item(new_item)

    update_user_info(new_order)
    # generate_pdf(order_no)
    send_order_confirmation(telephone_no, sorted_items, order.amount_paid, order_no)

    return {
        "status": "success",
        "order_no": order_no,
        "message": "Order created successfully"
    }