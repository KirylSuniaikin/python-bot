import logging

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from app.google_sheets import get_menu_items, get_all_extra_ingr, get_user_id
from app.models.models import OrderTO
from app.services.order_service import create_new_order
from app.whatsapp import send_ready_message

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/createOrder", methods=["POST"])
def create_order():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400

        try:
            # id=data["user_id"]
            order = OrderTO(
                # type=data["type"],
                user_id=data["user_id"],
                amount_paid=data["amount_paid"],
                items=data["items"]
            )
        except KeyError as e:
            return jsonify({"error": f"Missing required field: {e}"}), 400

        logging.info(f"Creating new order: {order}")
        response = create_new_order(order)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/sendReadeMessage", methods=["POST"])
def ready_message():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400

        try:
            tel = data["tel"]
            orderId = data["order_id"]
            logging.info(f"Sending ready message to: {tel}")
            response = send_ready_message(tel, get_user_id(tel))
        except KeyError as e:
            return jsonify({"error": f"Missing required field: {e}"}), 400

        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/createOrUpdateUser", methods=["POST"])
def createOrUpdateUser():
    logging.info("Creating or updating user")
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400
        tel = data["tel"]
        # logging.info(f"Sending ready message to: {tel}")
        # response = send_ready_message(tel, get_user_id(tel))
        return jsonify("response"), 200
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {e}"}), 400

    # try:
    #     data = request.json
    #     if not data:
    #         return jsonify({"error": "Invalid request, JSON data required"}), 400
    #
    #     try:
    #         tel = data["tel"]
    #         logging.info(f"Sending ready message to: {tel}")
    #         response = send_ready_message(tel, get_user_id(tel))
    #     except KeyError as e:
    #         return jsonify({"error": f"Missing required field: {e}"}), 400
    #
    #     return jsonify(response), 200
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500


@api_blueprint.route("/getAllMenuItems", methods=["GET"])
@cross_origin()
def get_menu():
    menu_items = get_menu_items()
    return jsonify([item.__dict__ for item in menu_items])


@api_blueprint.route("/getAllExtraIngr", methods=["GET"])
@cross_origin()
def get_extra_ingr():
    extra_ingr = get_all_extra_ingr()
    return jsonify([item.__dict__ for item in extra_ingr])

