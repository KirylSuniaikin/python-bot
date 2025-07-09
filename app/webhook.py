import logging
from flask import Blueprint, request, jsonify
from app.whatsapp import (ask_for_name, send_menu_utility)
from .repositories.repository import add_new_user, set_wait_for_name, is_wait_for_name, save_user_name, user_exists, \
    user_has_name

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

            if not user_exists(sender_phone):
                add_new_user(sender_phone, "")
                logging.info(f"New user {sender_phone} added")
                ask_for_name(sender_phone)
                set_wait_for_name(sender_phone, 1)
                return jsonify({"status": "asked for name"}), 200

            if is_wait_for_name(sender_phone) and not user_has_name(sender_phone):
                logging.info(f"User {sender_phone} entered name: {message_text}")
                save_user_name(sender_phone, message_text)
                set_wait_for_name(sender_phone, 0)
                send_menu_utility(sender_phone)
                return jsonify({"status": "name saved, menu sent"}), 200

            if not user_has_name(sender_phone):
                logging.info(f"Asking {sender_phone} for name again")
                ask_for_name(sender_phone)
                set_wait_for_name(sender_phone, 1)
                return jsonify({"status": "asked for name again"}), 200

            send_menu_utility(sender_phone)
            return jsonify({"status": "menu sent"}), 200

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
