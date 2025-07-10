import logging
from dotenv import load_dotenv
import requests
import os
from app.repositories.repository import get_user_id

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")


def build_order_message(order_id, sorted_items, total_amount):
    order_summary_lines = []

    for item in sorted_items:
        quantity = item.get("quantity", 1)
        name = item["name"].strip()
        size = item.get("size", "")
        category = item.get("category", "")

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


def send_order_confirmation(telephone_no, message_body, total_amount, order_id):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telephone_no,
        # "to": "48512066441",
        "type": "template",
        "template": {
            "name": "order_confirm",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "order_confirm",
                            "text": f"✅Got it! Your order {order_id} is confirmed!"
                        }
                    ]
                },
                {
                    "type": "BODY",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "total_price",
                            "text": f"{total_amount}"
                        },
                        {
                            "type": "text",
                            "parameter_name": "orderbody",
                            "text": f"{message_body}"
                        }
                    ]
                }
            ]
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        logging.info(f"Sent confirmation : {response.status_code}, Response: {response.text}")
        return response
    except Exception as e:
        logging.exception(f"Failed to send order to kitchen {e}")
        raise


def send_order_to_kitchen_text2(order_id, message_body, telephone_no, isEdit, name):
    # logging.info(f"Sending order to kitchen: {order_id}, items: {sorted_items}, total: {total_amount}")
    responses = []
    phones = ["97333607710", "97334344772"]
    for phone in phones:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "template",
            "template": {
                "name": "order_info2",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "HEADER",
                        "parameters": [
                            {
                                "type": "text",
                                "parameter_name": "header",
                                "text": f"{'✅ New order:' if not isEdit else '✏️ Order'} {order_id}{' updated!' if isEdit else '!'}"
                            }
                        ]
                    },
                    {
                        "type": "BODY",
                        "parameters": [
                            {
                                "type": "text",
                                "parameter_name": "client_info",
                                "text": f"{telephone_no} ({name})"
                            },
                            {
                                "type": "text",
                                "parameter_name": "orderbody",
                                "text": f"{message_body}"
                            }
                        ]
                    }
                ]
            }
        }
        try:
            url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            logging.info(f"Sent to {phone} : {response.status_code}, Response: {response.text}")
            responses.append(response)
        except Exception as e:
            logging.exception(f"Failed to send to {phone}: {e}")
            responses.append(None)
    return responses

# def send_info_to_kitchen(order_id):
#     url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
#     headers = {
#         "Authorization": f"Bearer {ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         # "to": "97333607710",
#         "to": "48512066441",
#         "type": "template",
#         "template": {
#             "name": "send_to_kitchen4",
#             "language": {"code": "en"},
#             "components": [
#                 {
#                     "type": "HEADER",
#                     "parameters": [
#                         {
#                             "type": "text",
#                             "parameter_name": "header",
#                             "text": f"Order {order_id}!"
#                         }
#                     ]
#                 },
#                 {
#                     "type": "BODY",
#                     "parameters": [
#                         {
#                             "type": "text",
#                             "parameter_name": "id",
#                             "text": f"{order_id}"
#                         }
#                     ]
#                 },
#                 {
#                     "type": "BUTTON",
#                     "sub_type": "url",
#                     "index": 0,
#                     "parameters": [
#                         {
#                             "type": "text",
#                             "text": str(order_id)
#                         }
#                     ]
#                 }
#             ]
#         }
#     }
#
#     response = requests.post(url, json=payload, headers=headers)
#     logging.info(f"Sent info to kitchen : {response.status_code}, Response: {response.text}")
#     return response


def build_kitchen_message(sorted_items):
    order_parts = []

    for item in sorted_items:
        quantity = item["quantity"]
        name = item["name"]
        size = item["size"]
        desc = item.get("description", "")

        details = [x.strip() for x in desc.split("+") if x.strip() and x.strip() != "'"]
        desc_text = f" ({' + '.join(details)})" if details else ""

        part = f"{quantity}x - *{name}* ({size}){desc_text}"
        order_parts.append(part)

    order_items_text = " | ".join(order_parts)
    return order_items_text


def send_ready_message(recipient_phone, user_name, user_id):
    if user_name is None:
        user_name = "Habibi"
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        # "to": "420601053179",
        "type": "template",
        "template": {
            "name": "last_confirm",
            "language": {"code": "en"},
            "components": [
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
                    "index": 0,
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


def send_menu_utility(recipient_phone):
    user_id = get_user_id(recipient_phone)
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        # "to": "48512066441",
        "type": "template",
        "template": {
            "name": "name_confirmed22",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "Habibi, order online, it's quick & super easy! 🍕"
                        }
                    ]
                },
                {
                    "type": "BODY",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "Tested on my grandma😄"
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
        # "to": "48512066441",
        "type": "text",
        "text": {
            "body": "Salam Aleikum 👋!\n"
                    "I'm Hamoody, IC Pizza Bot 🤖\n"
                    "Send me your name so I can share the menu with you 🍕\n"

        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent name request to {recipient_phone}: {response.status_code}")
