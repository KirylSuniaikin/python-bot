import logging
from dotenv import load_dotenv
import requests
import os

from app.google_sheets import get_user_id, get_user_name

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")


def send_order_confirmation(phone_number, sorted_items, total_amount, order_id):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    message_body = build_order_message(order_id, sorted_items, total_amount)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_body}
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent order confirmation to {phone_number}: {response.status_code}, Response: {response.text}")


def build_order_message(order_id, sorted_items, total_amount):
    order_summary_lines = []

    for item in sorted_items:
        quantity = item.get("quantity", 1)
        name = item["name"].strip()
        size = item.get("size", "")
        category = item.get("category", "")

        is_garlic_crust = item.get("isGarlicCrust", False)
        is_thin_dough = item.get("isThinDough", False)
        desc = item.get("description", "").strip()

        details_block = []

        if category == "Combo Deals" and ";" in desc:
            combo_parts = desc.split(";")
            for part in combo_parts:
                lines = part.strip().split("+")
                main = lines[0].strip()
                extras = [f"+{x.strip()}" for x in lines[1:] if x.strip()]
                formatted = f"    *{main}*\n" + "\n".join([f"      {e}" for e in extras])
                details_block.append(formatted)
        else:
            details = []

            if desc:
                desc_clean = desc.replace(";", "")
                details += [x.strip() for x in desc_clean.split("+") if x.strip() and x.strip() != "'"]
            if is_garlic_crust:
                details.append("Garlic Crust")
            if is_thin_dough:
                details.append("Thin Dough")

            if details:
                details_block.append("\n".join([f"    +{d}" for d in details]))

        title = f"{quantity}x *{name}*"
        if size:
            title += f" ({size})"

        full_line = title
        if details_block:
            full_line += "\n" + "\n".join(details_block)

        order_summary_lines.append(full_line)

    order_body = "\n".join(order_summary_lines)

    message_body = f"""
✅ *Got it! Your order {order_id} is confirmed!*

{order_body}

💰 Total: {total_amount:.3f} BHD
Thank you! See you soon! 🍕
""".strip()

    return message_body


def send_order_to_kitchen_text(order_id, sorted_items, total_amount):
    logging.info(f"Sending order to kitchen: {order_id}, items: {sorted_items}, total: {total_amount}")
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    message_body = build_kitchen_message(order_id, sorted_items, total_amount)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        # "to": "48512066441",
        "to": "97333607710",
        "type": "text",
        "text": {"body": message_body}
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent order confirmation to kitchen: {response.status_code}, Response: {response.text}")


def send_info_to_kitchen(order_id):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "97333607710",
        # "to": "48512066441",
        "type": "template",
        "template": {
            "name": "send_to_kitchen4",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "header",
                            "text": f"Order {order_id}!"
                        }
                    ]
                },
                {
                    "type": "BODY",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "id",
                            "text": f"{order_id}"
                        }
                    ]
                },
                {
                    "type": "BUTTON",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(order_id)
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent info to kitchen : {response.status_code}, Response: {response.text}")
    return response


def build_kitchen_message(order_id, sorted_items, total_amount):
    order_summary_lines = []

    for item in sorted_items:
        quantity = item.get("quantity", 1)
        name = item["name"].strip()
        size = item.get("size", "")
        category = item.get("category", "")

        is_garlic_crust = item.get("isGarlicCrust", False)
        is_thin_dough = item.get("isThinDough", False)
        desc = item.get("description", "").strip()

        details_block = []

        if category == "Combo Deals" and ";" in desc:
            combo_parts = desc.split(";")
            for part in combo_parts:
                lines = part.strip().split("+")
                main = lines[0].strip()
                extras = [f"+{x.strip()}" for x in lines[1:] if x.strip()]
                formatted = f"    *{main}*\n" + "\n".join([f"      {e}" for e in extras])
                details_block.append(formatted)
        else:
            details = []

            if desc:
                desc_clean = desc.replace(";", "")
                details += [x.strip() for x in desc_clean.split("+") if x.strip() and x.strip() != "'"]
            if is_garlic_crust:
                details.append("Garlic Crust")
            if is_thin_dough:
                details.append("Thin Dough")

            if details:
                details_block.append("\n".join([f"    +{d}" for d in details]))

        title = f"{quantity}x *{name}*"
        if size:
            title += f" ({size})"

        full_line = title
        if details_block:
            full_line += "\n" + "\n".join(details_block)

        order_summary_lines.append(full_line)

    order_body = "\n".join(order_summary_lines)

    message_body = f"""
*New order {order_id}*!

{order_body}

💰 Total: {total_amount:.3f} BHD
""".strip()

    return message_body


def send_ready_message(recipient_phone, user_id):
    user_name = get_user_name(recipient_phone)
    if user_name is None:
        user_name = "Habibi"
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    logging.info(f"phone : {recipient_phone}")
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": "ready_message2",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "text",
                            "text": f"Thank you, {user_name}! Enjoy your food🤌"
                        }
                    ]
                },
                {
                    "type": "BODY",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "name",
                            "text": str(user_name)
                        }
                    ]
                },
                {
                    "type": "BUTTON",
                    "sub_type": "url",
                    "index": 1,
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(user_id)
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent ready message to {recipient_phone}, Response: {response.text}")
    return response


def send_menu(recipient_phone, namo):
    user_id = get_user_id(recipient_phone)
    if namo is None:
        namo = "Habibi"
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    logging.info(f"User ID: {user_id}")
    logging.info(f"User name: {namo}")
    logging.info(f"Recipient phone: {recipient_phone}")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": "send_menu2",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "header",
                            "text": f"{namo}🤝"
                        }
                    ]
                },
                {
                    "type": "BODY",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "smiles",
                            "text": "🍕🥤"
                        }
                    ]
                },
                {
                    "type": "BUTTON",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": str(user_id)}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent menu message to {recipient_phone}: {response.status_code}, Response: {response.text}")


def ask_for_name(recipient_phone):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {
            "body": "Salam Aleikum 👋!\n"
                    "I’m Hamood, IC Pizza Bot 🤖, your friendly assistant to make ordering super easy and fast!\n"
                    "Glad to have you here!\n"
                    "What’s your name? 😊"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent name request to {recipient_phone}: {response.status_code}")
