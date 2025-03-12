import logging
import uuid
from datetime import datetime

from app.google_sheets import add_new_order, add_new_order_item, get_user_phone_number, update_user_info
from app.models.models import OrderTO, Order, OrderItem
from app.whatsapp import send_order_confirmation


def create_new_order(order: OrderTO):
    order_no = str(uuid.uuid4())[:8]
    telephone_no = get_user_phone_number(order.user_id) or "Error: unknown customer"
    address = ""
    order_items = order.items

    sorted_items = sorted(order_items, key=lambda x: ["Combo Deal", "Pizzas", "Sides", "Beverages"].index(x["category"]))
    logging.info(f"We are here")
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

    order_summary = []

    for item in sorted_items:
        category = item["category"]
        size = f"({item['size']})" if category in ["Combo Deals", "Pizza"] and item["size"] else ""
        description = item.get("description", "")
        is_garlic_crust = item.get("isGarlicCrust", False) if item["category"] == "Pizzas" or item["category"] == "Combo Deals" else ""
        is_thin_dough = item.get("isThinDough", False) if item["category"] == "Pizzas" or item["category"] == "Combo Deals" else ""
        is_garlic_crust_text = "Garlic Crust" if item.get("isGarlicCrust", False) else ""
        is_thin_dough_text = "Thin Dough" if item.get("isThinDough", False) else ""

        details = []
        if description:
            details.append(description)
        if is_garlic_crust:
            details.append(is_garlic_crust_text)
        if is_thin_dough:
            details.append(is_thin_dough_text)

        details_text = "\n   - " + "\n   - ".join(details) if details else ""

        order_summary.append(f" *{item['name']}* {size} - {item['amount']:.3f} BHD{details_text}")

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
    send_order_confirmation(telephone_no, order_summary, order.amount_paid)

    return {
        "status": "success",
        "order_no": order_no,
        "message": "Order created successfully"
    }
