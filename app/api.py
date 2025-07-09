import logging
import threading
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin

from app.models.models import OrderTO
from app.repositories.repository import make_order_ready, get_history_orders, get_user_info, \
    update_menu_tems_availability, update_dough_availability, update_brick_pizza_availability, update_payment
from app.services.cache import load_menu_cache, load_extra_ingr_cache
from app.services.order_service import create_new_order, get_all_active_orders, update_order, \
    async_ready_order_post_processing

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
            notes = data.get("notes", "")

            order = OrderTO(
                type=order_type,
                tel=tel,
                user_id=user_id,
                amount_paid=amount_paid,
                payment_type=payment_type,
                items=items,
                notes=notes
            )
        except KeyError as e:
            return jsonify({"error": f"Missing required field: {e}"}), 400

        response = create_new_order(order, data.get("customer_name"))
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
            id = request.args.get("id")
            tel = data.get("tel")
            user_id = data.get("user_id")
            amount_paid = data["amount_paid"]
            items = data["items"]
            payment_type = data.get("payment_type")
            notes = data.get("notes", "")
            logging.info("Notes: " + notes)

            order = OrderTO(
                id=int(id),
                type=data.get("delivery_method", ""),
                order_no=data.get("order_no"),
                tel=tel,
                user_id=user_id,
                address=data.get("address"),
                amount_paid=amount_paid,
                items=items,
                payment_type=payment_type,
                notes=notes
            )
        except KeyError as e:
            return jsonify({"error": f"Missing required field: {e}"}), 400

        response = update_order(order)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/getAllActiveOrders", methods=["GET"])
def get_all_active_orders_v1():
    print("lol")
    try:
        active_orders = get_all_active_orders()
        return jsonify(active_orders)
    except Exception as e:
        logging.exception("Error in get_active_orders")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/getHistory", methods=["GET"])
def get_history():
    try:
        history_orders = get_history_orders()
        return jsonify(history_orders)
    except Exception as e:
        logging.exception("Error in get_history")
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/updatePaymentType', methods=['POST'])
def update_payment_type():
    data = request.json
    order_id = data.get('order_id')
    new_payment_type = data.get('payment_type')

    if not order_id or not new_payment_type:
        return jsonify({"error": "Missing order_id or payment_type"}), 400
    update_payment(order_id, new_payment_type)

    return jsonify({"status": "ok", "message": "Payment type updated successfully"})


@api_blueprint.route("/readyAction", methods=["POST"])
def ready_action():
    try:
        order_id = request.args.get("id")
        if not order_id:
            return jsonify({"error": "Missing orderId in query params"}), 400

        order = make_order_ready(order_id)
        if order.telephone_no is not None and order.telephone_no != "Unknown customer":
            appctx = current_app.app_context()
            threading.Thread(target=async_ready_order_post_processing, args=(appctx, order)).start()

        return jsonify({"status": "ok", "message": f"Order {order_id} marked as ready."})
    except Exception as e:
        logging.exception("Error in ready_action")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/updateAvailability', methods=['POST'])
def update_availability():
    data = request.json
    changes = data.get('changes', [])

    for change in changes:
        type_ = change.get('type')
        name_or_dough = change.get('name')
        enabled = change.get('enabled', True)

        if type_ == 'group':
            update_menu_tems_availability(name_or_dough, enabled)
        elif type_ == 'dough':
            if name_or_dough == "Brick dough":
                update_brick_pizza_availability(enabled)
            else:
                update_dough_availability(name_or_dough, enabled)
    current_app.menu_cache = []
    current_app.extra_ingr_cache = []

    return jsonify({"status": "ok", "message": "Availability updated successfully"})


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


@api_blueprint.route("/getBaseAppInfo", methods=["GET"])
@cross_origin()
def get_base_app_info():
    user_id = request.args.get("userId")

    if not hasattr(current_app, "menu_cache") or not current_app.menu_cache:
        load_menu_cache()
    if not hasattr(current_app, "extra_ingr_cache") or not current_app.extra_ingr_cache:
        load_extra_ingr_cache()
    response = {
        "menu": current_app.menu_cache,
        "extraIngr": current_app.extra_ingr_cache
    }
    if user_id:
        userInfo = get_user_info(user_id)
        response["userInfo"] = {
            "name": userInfo["name"] or "Unknown user",
            "phone": userInfo["phone"]
        }

    return jsonify(response)