import logging
from flask import jsonify


# def create_update_user(tel, order_id):
#     if user_exists(tel):
#         logging.info(f"User {tel} exists")
#         update_user_info(get_order_by_id(order_id))
#     else:
#         logging.info(f"User {tel} does not exist")
#         add_new_user(tel, "")
#         update_user_info(get_order_by_id(order_id))
#     return jsonify("response"), 200