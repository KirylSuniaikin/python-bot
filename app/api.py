import logging
import threading
from datetime import datetime

import pytz
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from sqlalchemy import func
from app.conf.db_conf import db
from dateutil import parser

from app.models.models import OrderTO, EventType, Event
from app.repositories.repository import make_order_ready, get_history_orders, get_user_info, \
    update_menu_tems_availability, update_dough_availability, update_brick_pizza_availability, update_payment, \
     get_retention_metric, get_customer_stats, get_arpu_aov, get_orders_with_customers_for_period, get_latest_stage, get_open_shift_cash, get_total_cash_orders

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

@cross_origin()
@api_blueprint.route("/getAllActiveOrders", methods=["GET"])
def get_all_active_orders_v1():
    print("lol")
    try:
        active_orders = get_all_active_orders()
        return jsonify(active_orders)
    except Exception as e:
        logging.exception("Error in get_active_orders")
        return jsonify({"error": str(e)}), 500

@cross_origin()
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
        "extraIngr": current_app.extra_ingr_cache,
    }
    if user_id:
        userInfo = get_user_info(user_id)
        response["userInfo"] = {
            "name": userInfo["name"] or "Unknown user",
            "phone": userInfo["phone"]
        }

    return jsonify(response)

@api_blueprint.route('/get_statistics', methods=['GET'])
@cross_origin()
def get_statistics():
    start_date = request.args.get('start_date')
    finish_date = request.args.get('finish_date')
    certain_date = request.args.get('certain_date')

    if not start_date or not finish_date:
        return jsonify({"error": "Missing start_date or finish_date"}), 400

    orders_with_customers = get_orders_with_customers_for_period(start_date, finish_date)

    new_customer_order_count = 0
    old_customer_order_count = 0
    total_revenue = 0

    for order, amount_of_orders in orders_with_customers:
        total_revenue += order.amount_paid

        if amount_of_orders is None or amount_of_orders <= 1:
            new_customer_order_count += 1
        else:
            old_customer_order_count += 1

    arpu_aov = get_arpu_aov()
    retention_metric = get_retention_metric(certain_date)
    customer_stats = get_customer_stats()

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_order_count": new_customer_order_count+old_customer_order_count,
        "new_customer_ordered_count": new_customer_order_count,
        "old_customer_ordered_count": old_customer_order_count,
        "ARPU": arpu_aov["ARPU"],
        "unique_customers_all_time": customer_stats["unique_customers_all_time"],
        "repeat_customers_all_time": customer_stats["repeat_customers_all_time"],
        "average_order_value_all_time": arpu_aov["AOV"],
        "month_total_customers": retention_metric["month_total_customers"],
        "retained_customers": retention_metric["retained_customers"],
        "retention_percentage": round(retention_metric["retention_percentage"], 2) if retention_metric["retention_percentage"] else None
    })

@api_blueprint.route("/sendShiftEvent", methods=["POST"])
@cross_origin()
def create_event():
    data = request.json
    print(">>> RAW JSON from client:", data)
    branch_id = data["branch_id"]
    event_type = EventType[data["type"]]

    last_shift_no = db.session.query(func.max(Event.shift_no))\
        .filter_by(branch_id=branch_id).scalar()

    if event_type == EventType.OPEN_SHIFT_CASH_CHECK:
        shift_no = (last_shift_no or 0) + 1
    else:
        if not last_shift_no:
            return jsonify({"error": "no shift started yet"}), 400
        shift_no = last_shift_no

    cash_warning = None

    if event_type == EventType.CLOSE_SHIFT_CASH_CHECK:
        entered_cash = data.get("cash_amount")
        initial_cash = get_open_shift_cash(branch_id)
        logging.info(f"[CASH CHECK] ✅ Found OPEN_SHIFT_CASH_CHECK: {initial_cash}")
        orders_total = get_total_cash_orders()
        logging.info(f"[CASH CHECK] 💸 Sum of CASH orders: {orders_total}")
        expected_cash = round(initial_cash + orders_total, 2)
        expected_cash_today = initial_cash + orders_total

        if round(entered_cash, 2) != expected_cash:
            cash_warning = {
                "error": "Amounts doesn't match",
                "expected": expected_cash_today
            }


    event = Event(
        type=event_type,
        datetime=datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M"),
        prep_plan=data.get("prep_plan"),
        cash_amount=data.get("cash_amount"),
        branch_id=branch_id,
        shift_no=shift_no
    )
    logging.info(event.datetime)

    db.session.add(event)
    db.session.commit()

    response = {
        "status": "created",
        "id": event.id,
        "shiftNo": shift_no,
    }

    if cash_warning:
        response["cashWarning"] = cash_warning
    logging.info(response)

    return jsonify(response)

@api_blueprint.route("/getLastStage", methods=["GET"])
@cross_origin()
def get_last_stage():
    branch_id = request.args.get("branchId")
    if not branch_id:
        return jsonify({"error": "branchId is required"}), 400

    latest_stage = get_latest_stage(branch_id)
    return jsonify({"type": latest_stage})
