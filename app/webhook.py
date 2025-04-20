import logging
from flask import Blueprint, request, jsonify
from app.whatsapp import (send_menu, ask_for_name)
from .google_sheets import add_new_user, user_exists, save_user_name, user_has_name, \
    get_user_name

webhook_blueprint = Blueprint("webhook", __name__)


@webhook_blueprint.route("/", methods=["POST"], strict_slashes=False)
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
                logging.info(f"User {sender_phone} entered name: {message_text}")
                save_user_name(sender_phone, message_text)
                logging.info(f"User {sender_phone} entered name: {message_text}")
                send_menu(sender_phone, get_user_name(sender_phone))

        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@webhook_blueprint.route("/", methods=["GET"])
def webhook_get():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        mode = request.args.get("hub.mode")
        return str(challenge), 200
