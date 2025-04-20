import logging

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from app.google_sheets import get_menu_items, get_all_extra_ingr, get_user_id, get_user_phone_by_order_id, \
    make_order_ready
from app.models.models import OrderTO
from app.services.customer_service import create_update_user
from app.services.order_service import create_new_order, get_all_active_orders, update_order
from app.whatsapp import send_ready_message

api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/privacy-policy")
def privacy_policy():
    return """
    <h1>Privacy Policy</h1>
    <p>This app does not collect or share personal user data.</p>
    """


@api_blueprint.route("/terms-of-service")
def terms_of_service():
    return """
    <h1>Terms of Service</h1>
    <p>By using this app, you agree to the basic usage rules and disclaimers.</p>
    """


@api_blueprint.route("/data-deletion")
def data_deletion():
    return """
    <h1>Data Deletion</h1>
    <p>If you want your data deleted, please contact us via email.</p>
    """


@api_blueprint.route("/createOrder", methods=["POST"])
def create_order():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400

        try:
            tel = data.get("tel")
            user_id = data.get("user_id")
            amount_paid = data["amount_paid"]
            items = data["items"]
            payment_type = data.get("payment_type", "")
            order_type = data.get("delivery_method", "Pick Up")

            order = OrderTO(
                type=order_type,
                tel=tel,
                user_id=user_id,
                amount_paid=amount_paid,
                payment_type=payment_type,
                items=items
            )
        except KeyError as e:
            return jsonify({"error": f"Missing required field: {e}"}), 400

        logging.info(f"Creating new order: {order}")
        response = create_new_order(order)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/editOrder", methods=["POST"])
def edit_order():
    try:
        logging.info(f"{request.json}")
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400

        try:
            order_id = request.args.get("orderId")
            tel = data.get("tel")
            user_id = data.get("user_id")
            amount_paid = data["amount_paid"]
            items = data["items"]
            payment_type = data.get("payment_type")

            order = OrderTO(
                type=data.get("delivery_method", ""),
                tel=tel,
                user_id=user_id,
                amount_paid=amount_paid,
                items=items,
                payment_type=payment_type
            )
        except KeyError as e:
            return jsonify({"error": f"Missing required field: {e}"}), 400

        logging.info(f"Updating order with id: {order_id}")
        response = update_order(order, order_id)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @api_blueprint.route("/sendReadeMessage", methods=["POST"])
# def ready_message():
#     try:
#         data = request.json
#         if not data:
#             return jsonify({"error": "Invalid request, JSON data required"}), 400
#
#         try:
#             tel = data["tel"]
#             logging.info(f"Sending ready message to: {tel}")
#             response = send_ready_message(tel, get_user_id(tel))
#         except KeyError as e:
#             return jsonify({"error": f"Missing required field: {e}"}), 400
#
#         return jsonify(response), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@api_blueprint.route("/getAllActiveOrders", methods=["GET"])
def get_active_orders_v1():
    try:
        active_orders = get_all_active_orders()
        return jsonify(active_orders)
    except Exception as e:
        logging.exception("Error in get_active_orders")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/readyAction", methods=["POST"])
def ready_action():
    try:
        order_id = request.args.get("orderId")
        if not order_id:
            return jsonify({"error": "Missing orderId in query params"}), 400

        logging.info(f"📦 Got click for orderId={order_id}")
        recipient_phone = get_user_phone_by_order_id(order_id)
        user_id = get_user_id(recipient_phone)
        send_ready_message(recipient_phone, user_id)
        make_order_ready(order_id)

        return jsonify({"status": "ok", "message": f"Order {order_id} marked as ready."})
    except Exception as e:
        logging.exception("Error in ready_action")
        return jsonify({"error": str(e)}), 500


# @api_blueprint.route("/generateCheck", methods=["POST"])
# def generate_check():
#     try:
#         data = request.json
#         if not data:
#             return jsonify({"error": "Invalid request, JSON data required"}), 400
#         try:
#             orderId = data["order_id"]
#             logging.info(f"Generating check for order: {orderId}")
#             generate_pdf(orderId)
#         except KeyError as e:
#             return jsonify({"error": f"Missing required field: {e}"}), 400
#
#         return jsonify("response"), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@api_blueprint.route("/createOrUpdateUser", methods=["POST"])
def createOrUpdateUser():
    logging.info("Creating or updating user")
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, JSON data required"}), 400
        tel = data["tel"]
        order_id = data["order_id"]
        create_update_user(tel, order_id)
        return jsonify("response"), 200
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {e}"}), 400


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

