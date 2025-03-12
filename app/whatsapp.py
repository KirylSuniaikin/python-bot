import logging
from dotenv import load_dotenv
import requests
import os

from app.google_sheets import get_user_id

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")


def send_order_confirmation(phone_number, order_summary, total_amount):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    message_body = f"""
        ✅ *Order Confirmation*
        Your order:
        {chr(10).join(order_summary)}
        
        💰 *Total: {total_amount:.3f} BHD*
        Thank you! We are processing your order. 🍕
            """.strip()

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_body}
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent order confirmation to {phone_number}: {response.status_code}, Response: {response.text}")


def send_ready_message(recipient_phone, user_id):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    message_header = "Enjoy you meal! 🍕🎉"
    logging.info(f"phone : {recipient_phone}")
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "template",
        "template": {
            "name": "ready_message",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "text",
                            "text": message_header}
                    ]
                },
                {
                    "type": "BUTTON",
                    "sub_type": "url",
                    "index": 1,
                    "parameters": [
                        {"type": "text", "text": str(user_id)}
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
            "name": "send_menu",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "HEADER",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "header",
                            "text": f"{namo}👋"
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
                        {"type": "text", "text": str(user_id)}
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
            "body": "Hey there! I’m IC Pizza Bot 🤖—that’s what the programmers named me. I don’t think we’ve met yet! What’s your name? 😊"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"Sent name request to {recipient_phone}: {response.status_code}")


# def log_http_response(response):
#     logging.info(f"Status: {response.status_code}")
#     logging.info(f"Content-type: {response.headers.get('content-type')}")
#     logging.info(f"Body: {response.text}")
#
#
# def get_text_message_input(recipient, text):
#     return json.dumps(
#         {
#             "messaging_product": "whatsapp",
#             "recipient_type": "individual",
#             "to": recipient,
#             "type": "text",
#             "text": {"preview_url": False, "body": text},
#         }
#     )
#
#
# def generate_response(response):
#     # Return text in uppercase
#     return response.upper()


# def send_message(data):
#     headers = {
#         "Content-type": "application/json",
#         "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
#     }
#
#     url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
#
#     try:
#         response = requests.post(
#             url, data=data, headers=headers, timeout=10
#         )  # 10 seconds timeout as an example
#         response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
#     except requests.Timeout:
#         logging.error("Timeout occurred while sending message")
#         return jsonify({"status": "error", "message": "Request timed out"}), 408
#     except (
#         requests.RequestException
#     ) as e:  # This will catch any general request exception
#         logging.error(f"Request failed due to: {e}")
#         return jsonify({"status": "error", "message": "Failed to send message"}), 500
#     else:
#         # Process the response as normal
#         log_http_response(response)
#         return response
#

# def process_text_for_whatsapp(text):
#     # Remove brackets
#     pattern = r"\【.*?\】"
#     # Substitute the pattern with an empty string
#     text = re.sub(pattern, "", text).strip()
#
#     # Pattern to find double asterisks including the word(s) in between
#     pattern = r"\*\*(.*?)\*\*"
#
#     # Replacement pattern with single asterisks
#     replacement = r"*\1*"
#
#     # Substitute occurrences of the pattern with the replacement
#     whatsapp_style_text = re.sub(pattern, replacement, text)
#
#     return whatsapp_style_text


# def process_whatsapp_message(body):
#     wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
#     name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
#
#     message = body["entry"][0]["changes"][0]["value"]["messages"][0]
#     message_body = message["text"]["body"]
#
#     # TODO: implement custom function here
#     response = generate_response(message_body)
#
#     # OpenAI Integration
#     # response = generate_response(message_body, wa_id, name)
#     # response = process_text_for_whatsapp(response)
#
#     data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
#     send_message(data)


# def is_valid_whatsapp_message(body):
#     """
#     Check if the incoming webhook event has a valid WhatsApp message structure.
#     """
#     return (
#         body.get("object")
#         and body.get("entry")
#         and body["entry"][0].get("changes")
#         and body["entry"][0]["changes"][0].get("value")
#         and body["entry"][0]["changes"][0]["value"].get("messages")
#         and body["entry"][0]["changes"][0]["value"]["messages"][0]
#     )
