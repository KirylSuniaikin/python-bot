import logging
import json
from flask import Blueprint, request, jsonify, current_app
from .decorators.security import signature_required
from app.whatsapp import (send_menu, ask_for_name)
from .google_sheets import add_new_user, user_exists, save_user_name, user_has_name, \
    get_user_name

webhook_blueprint = Blueprint("webhook", __name__)


@webhook_blueprint.route("/", methods=["POST"], strict_slashes=False)
@signature_required
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400

        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        if "messages" in value:
            message = value["messages"][0]
            sender_phone = value["contacts"][0]["wa_id"]
            message_text = message.get("text", {}).get("body", "").strip()

            if message_text.lower() == "hello":
                if not user_exists(sender_phone):
                    add_new_user(sender_phone)
                    logging.info("User was added")
                    ask_for_name(sender_phone)
                elif not user_has_name(sender_phone):
                    logging.info("User exists but has no name")
                    ask_for_name(sender_phone)
                else:
                    logging.info("User exists and has a name")
                    send_menu(sender_phone, get_user_name(sender_phone))

            elif user_exists(sender_phone) and not user_has_name(sender_phone):
                # Если юзер ещё не имеет имени, но отправил сообщение — считаем его именем
                logging.info(f"User {sender_phone} entered name: {message_text}")
                save_user_name(sender_phone, message_text)
                logging.info(f"User {sender_phone} entered name: {message_text}")
                send_menu(sender_phone, get_user_name(sender_phone))  # Отправляем благодарность + кнопку "View Menu"


            # # 2️⃣ Если пользователь нажал кнопку
            # elif "button" in message:
            #     button_id = message["button"]["payload"]
            #     logging.info(f"User {sender_phone} clicked button: {button_id}")
            #
            #     if button_id == "view_menu":
            #         # send_menu(sender_phone)  # Высылаем меню
            #         return jsonify({"status": "menu_sent"}), 200

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500






#

#
#
# @webhook_blueprint.route("/", methods=["POST"])
# @signature_required
# def webhook_post():
#     logging.info("Received a POST request")
#     return handle_message()


#     def handle_message():
#         """
#         Handle incoming webhook events from the WhatsApp API.
#
#         This function processes incoming WhatsApp messages and other events,
#         such as delivery statuses. If the event is a valid message, it gets
#         processed. If the incoming payload is not a recognized WhatsApp event,
#         an error is returned.
#
#         Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.
#
#         Returns:
#             response: A tuple containing a JSON response and an HTTP status code.
#         """
#     body = request.get_json()
#     # logging.info(f"request body: {body}")
#
#     # Check if it's a WhatsApp status update
#     if (
#             body.get("entry", [{}])[0]
#                     .get("changes", [{}])[0]
#                     .get("value", {})
#                     .get("statuses")
#     ):
#         logging.info("Received a WhatsApp status update.")
#         return jsonify({"status": "ok"}), 200
#
#     try:
#         if is_valid_whatsapp_message(body):
#             process_whatsapp_message(body)
#             return jsonify({"status": "ok"}), 200
#         else:
#             # if the request is not a WhatsApp API event, return an error
#             return (
#                 jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
#                 404,
#             )
#     except json.JSONDecodeError:
#         logging.error("Failed to decode JSON")
#         return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400
#
#
# # Required webhook verifictaion for WhatsApp
# def verify():
#     # Parse params from the webhook verification request
#     mode = request.args.get("hub.mode")
#     token = request.args.get("hub.verify_token")
#     challenge = request.args.get("hub.challenge")
#     # Check if a token and mode were sent
#     if mode and token:
#         # Check the mode and token sent are correct
#         if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
#             # Respond with 200 OK and challenge token from the request
#             logging.info("WEBHOOK_VERIFIED")
#             return challenge, 200
#         else:
#             # Responds with '403 Forbidden' if verify tokens do not match
#             logging.info("VERIFICATION_FAILED")
#             return jsonify({"status": "error", "message": "Verification failed"}), 403
#     else:
#         # Responds with '400 Bad Request' if verify tokens do not match
#         logging.info("MISSING_PARAMETER")
#         return jsonify({"status": "error", "message": "Missing parameters"}), 400
#
