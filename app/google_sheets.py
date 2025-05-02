import logging
import os
import uuid
import pytz
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.models.models import MenuItem, OrderItem, Order, Customer, ExtraIngr, OrderTO, Check

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_ID = "11tLnA8whcBHykGf8OmuOwmacbvons4BIHx7ZjvteNX0"
ORDERS_SHEET_ID = 36417195
ORDER_ITEMS_SHEET_ID = 447066114
MENU_ITEMS_SHEET_ID = 1153080402
CUSTOMERS_SHEET_ID = 821617987
EXTRA_INGR_SHEET_ID = 2019426420

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
creds_path = os.path.join(BASE_DIR, "..", "google_sheets_cred.json")
creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
client = gspread.authorize(creds)
drive_service = build("drive", "v3", credentials=creds)


menu_items_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(MENU_ITEMS_SHEET_ID)
orders_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(ORDERS_SHEET_ID)
order_items_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(ORDER_ITEMS_SHEET_ID)
customers_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(CUSTOMERS_SHEET_ID)
extra_ingr_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(EXTRA_INGR_SHEET_ID)


def make_order_ready(order_id):
    logging.info(f"Making order {order_id} ready")
    data = orders_sheet.get_all_records()

    for index, row in enumerate(data, start=2):
        if str(row["Order No"]).strip() == str(order_id).strip():
            orders_sheet.update_cell(index, 3, "Ready")
            logging.info(f"Order {order_id} marked as ready")
            break
    else:
        logging.error(f"Order {order_id} not found")


# def get_order_data(order_id):
#     logging.info(f"Getting order data for order_id: {order_id}")
#     orders = orders_sheet.get_all_records()
#     order_items = order_items_sheet.get_all_records()
#
#     order_data = next((order for order in orders if str(order["Order No"]) == str(order_id)), None)
#
#     if not order_data:
#         logging.error(f"Order data not found for order_id: {order_id}")
#         return None
#
#     items = [
#         OrderItem(
#             order_no=item["Order No"],
#             id=item["ID"],
#             name=item["Name"],
#             quantity=int(item["Quantity"]),
#             amount=float(item["Amount"]),
#             size=item["Size"],
#             category=item["Category"],
#             isGarlicCrust=str(item["isGarlicCrust"]).strip().lower() == "true",
#             isThinDough=str(item["isThinDough"]).strip().lower() == "true",
#             description=item["Description"],
#
#         )
#         for item in order_items if str(item["Order No"]) == str(order_id)
#     ]
#
#     check = Check(
#         order_id=order_id,
#         total=float(order_data["Amount paid"]),
#         items=items,
#         date=order_data["Date and Time"]
#     )
#     logging.info(f"Check created: {check.total}")
#     return check


def save_check_link(order_id, link):
    data = orders_sheet.get_all_records()

    for index, row in enumerate(data, start=2):
        if str(row["Order No"]) == str(order_id):
            orders_sheet.update_cell(index, 8, link)
            logging.info(f"Check link saved for order_id: {order_id}")
            break


# def get_order_by_id(order_id):
#     data = orders_sheet.get_all_records()
#
#     for row in data:
#         if str(row["Order No"]) == str(order_id):
#             return Order(
#                 order_no=row["Order No"],
#                 telephone_no=row["Telephone No"],
#                 status=row["Status"],
#                 date_and_time=row["Date and Time"],
#                 type=row["Type"],
#                 address=row["Address"],
#                 amount_paid=row["Amount paid"],
#                 notes=row["Notes"]
#             )
#
#     return None


def save_user_name(phone_number, name):
    cell = customers_sheet.find(phone_number)
    if cell:
        customers_sheet.update_cell(cell.row, 3, name)


def update_user_info(order: Order, user_name):
    data = customers_sheet.get_all_records()
    user_row_index = None

    for i, row in enumerate(data, start=2):
        if str(row["Telephone No"]) == str(order.telephone_no):
            user_row_index = i
            break
    if user_row_index is None:
        logging.warning(f"User with phone {order.telephone_no} not found in Google Sheets.")
        return

    current_orders = int(row.get("Amount of orders", 0))
    current_amount_paid = float(row.get("Amount Paid", 0))

    new_orders_count = current_orders + 1
    new_total_paid = current_amount_paid + order.amount_paid
    current_date = datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M")

    customers_sheet.update(
        f"E{user_row_index}",
        [[new_orders_count, new_total_paid, current_date]]
    )
    logging.info(user_row_index)
    logging.info(user_name)
    customers_sheet.update(f"C{user_row_index}", [[user_name]])

    logging.info(f"Updated user {order.telephone_no}: Orders={new_orders_count}, Amount Paid={new_total_paid}, Last Order={current_date}")


def edit_user_info(order: OrderTO, orderId: str):
    orders = orders_sheet.get_all_records()
    customers = customers_sheet.get_all_records()
    old_order = None
    for index, row in enumerate(orders, start=2):
        if str(row["Order No"]) == orderId:
            old_order = row
            break
    if not old_order:
        logging.warning(f"Order with ID {orderId} not found.")
        return
    phone_number = old_order.get("Telephone No", "")
    if not phone_number:
        logging.warning(f"No phone number found for order {orderId}")
        return
    logging.info(f"Phone number: {phone_number}")
    user_row_index = None
    user_row = None
    for i, row in enumerate(customers, start=2):
        if str(row["Telephone No"]).strip() == str(phone_number).strip():
            user_row_index = i
            user_row = row
            break
    if not user_row_index:
        logging.warning(f"User with phone {phone_number} not found.")
        return
    old_amount_paid = float(old_order.get("Amount paid", 0))
    new_amount_paid = float(order.amount_paid)

    current_total_paid = float(user_row.get("Amount Paid", 0))
    updated_total_paid = current_total_paid - old_amount_paid + new_amount_paid
    current_date = datetime.now(pytz.timezone("Asia/Bahrain")).strftime("%Y-%m-%d %H:%M")

    customers_sheet.update(
        f"F{user_row_index}:G{user_row_index}",
        [[updated_total_paid, current_date]]
    )

    logging.info(f"User {phone_number} updated after order edit. Old paid: {old_amount_paid}, New paid: {new_amount_paid}, Total: {updated_total_paid}")
    return phone_number


def user_exists(phone_number):
    users_numbers = customers_sheet.col_values(2)
    return phone_number in users_numbers


def user_has_name(phone_number):
    data = customers_sheet.get_all_records()
    logging.info(f"Checking if user {phone_number} has a name")
    for row in data:
        if str(row["Telephone No"]).strip() == str(phone_number).strip():
            logging.info(f"User {phone_number} has name: {row['Name']}")
            return bool(row.get("Name"))
    return False


def get_user_phone_number(user_id):
    data = customers_sheet.get_all_records()
    for row in data:
        if str(row["ID"]).strip() == str(user_id).strip():
            return row["Telephone No"]
    return None


def get_user_phone_from_current_users(users, user_id):
    for user in users:
        if str(user["ID"]).strip() == str(user_id).strip():
            return user["Telephone No"]
    return None


def get_user_name(phone_number):
    data = customers_sheet.get_all_records()
    for row in data:
        if str(row["Telephone No"]).strip() == str(phone_number).strip():
            return row["Name"]
    return None


def get_user_name_from_current_users(users, phone_number):
    for user in users:
        if str(user["Telephone No"]).strip() == str(phone_number).strip():
            return user["Name"]
    return None


def get_user_id(phone_number):
    data = customers_sheet.get_all_records()
    for row in data:
        if str(row["Telephone No"]).strip() == str(phone_number).strip():
            return row["ID"]
    return None


def get_user_phone_by_order_id(order_id):
    data = orders_sheet.get_all_records()
    for row in data:
        if str(row["Order No"]).strip() == str(order_id).strip():
            return row["Telephone No"]
    return None


def add_new_user(phone_number, user_name):
    customer = Customer(
        id=str(uuid.uuid4())[:8],
        telephone_no=phone_number,
        name=user_name,
        address="",
        amount_of_orders=0,
        amount_paid=0,
        last_order=""
    )
    customers_sheet.append_row([
        customer.id,
        customer.telephone_no,
        customer.name,
        customer.address,
        customer.amount_of_orders,
        customer.amount_paid,
        customer.last_order
    ])


def get_menu_items():
    data = menu_items_sheet.get_all_records()
    menu_items = []

    for row in data:
        try:
            item = MenuItem(
                category=row["Category"],
                name=row["Name"],
                size=row["Size"],
                price=float(row["Price"]),
                photo=row["Photo"],
                item_id=int(row["ID"]),
                description=row["Description"],
                available=str(row["Available"]).strip().lower() == "true",
                isBestSeller=str(row["isBestSeller"]).strip().lower() == "true"
            )

            if item.available:
                menu_items.append(item)

        except Exception as e:
            print(f"Ошибка при обработке строки: {row}, {e}")

    return menu_items


def get_all_extra_ingr():
    data = extra_ingr_sheet.get_all_records()

    extra_ingr = []
    for row in data:
        try:
            item = ExtraIngr(
                name=row["Name"],
                price=float(row["Price"]),
                photo=row["Photo"],
                size=row["Size"],
                available=str(row["Available"]).strip().lower() == "true"
            )
            if item.available:
                extra_ingr.append(item)
        except Exception as e:
            print(f"Ошибка при обработке строки: {row}, {e}")

    return extra_ingr


def add_new_order(order: Order):
    orders_sheet.append_row([
        order.order_no,
        order.telephone_no,
        order.status,
        order.date_and_time,
        order.type,
        order.address,
        order.amount_paid,
        order.payment_type,
        # order.notes,
    ])


def add_new_order_item(item: OrderItem):
    order_items_sheet.append_row([
        item.order_no,
        item.name,
        item.quantity,
        item.amount,
        item.size,
        item.category,
        item.id,
        item.isGarlicCrust,
        item.isThinDough,
        item.description,
        item.sale_amount
    ])


def delete_order_info(order_id):
    orders = orders_sheet.get_all_records()
    order_items = order_items_sheet.get_all_records()
    for index, row in enumerate(orders, start=2):
        if str(row["Order No"]).strip().lower() == str(order_id).strip().lower():
            orders_sheet.delete_rows(index)
            logging.info(f"Order {order_id} deleted")
            break

    rows_to_delete = []
    for index1, row in enumerate(order_items, start=2):
        if str(row["Order No"]).strip().lower() == str(order_id).strip().lower():
            rows_to_delete.append(index1)

    for index in reversed(rows_to_delete):
        order_items_sheet.delete_rows(index)
        logging.info(f"Order item {order_id} deleted on row {index}")


def get_active_orders():
    orders = orders_sheet.get_all_records()
    order_items = order_items_sheet.get_all_records()
    users = customers_sheet.get_all_records()

    active_orders = []
    for order in orders:
        if str(order["Status"]).strip().lower() != "ready":
            order_id = order["Order No"]
            order_items_for_order = [item for item in order_items if str(item["Order No"]).strip().lower() == str(order_id)]

            items = []
            user_name = get_user_name_from_current_users(users, order.get("Telephone No", "")) or "Unknown customer"
            for item in order_items_for_order:
                photo_url = ger_photo_url_by_name(item["Name"])
                try:
                    items.append({
                        "name": item["Name"],
                        "quantity": int(item["Quantity"]),
                        "amount": float(item["Amount"]),
                        "size": item.get("Size", ""),
                        "category": item.get("Category", ""),
                        "isGarlicCrust": str(item.get("isGarlicCrust", "")).strip().lower() == "true",
                        "isThinDough": str(item.get("isThinDough", "")).strip().lower() == "true",
                        "description": item.get("Description", ""),
                        "discount_amount": item.get("Sale Amount", 0),
                        "photo": photo_url,
                    })
                except Exception as e:
                    print(f"Ошибка при обработке item: {item}, {e}")

            active_orders.append({
                "orderId": order_id,
                "order_type": order.get("Type", ""),
                "amount_paid": float(order.get("Amount paid", 0)),
                "phone_number": order.get("Telephone No", ""),
                "sale_amount": float(order.get("Sale Amount", 0)),
                "customer_name": user_name,
                "order_created": order.get("Date and Time", ""),
                "payment_type": order.get("Payment Type", ""),
                "notes": order.get("Notes", "Empty Note"),
                "items": items
            })

    return {"orders": active_orders}


def ger_photo_url_by_name(name):
    data = menu_items_sheet.get_all_records()
    for row in data:
        if str(row["Name"]).strip().lower() == str(name).strip().lower():
            return row["Photo"]
    logging.info(f"Photo URL for {name} not found")
    return None


def get_user_info(user_id):
    data = customers_sheet.get_all_records()
    phone = get_user_phone_from_current_users(data, user_id)
    username = get_user_name_from_current_users(data, phone)
    return {
        "phone": phone,
        "name": username
    }


from datetime import datetime, timedelta


def get_history_orders():
    orders = orders_sheet.get_all_records()
    order_items = order_items_sheet.get_all_records()
    users = customers_sheet.get_all_records()
    bahrain_tz = pytz.timezone("Asia/Bahrain")
    now = datetime.now(bahrain_tz)
    cutoff_time = now - timedelta(days=1)
    datetime_format = "%Y-%m-%d %H:%M"

    history_orders = []
    for order in orders:
        order_time_str = order.get("Date and Time", "")
        try:
            order_time = bahrain_tz.localize(datetime.strptime(order_time_str, datetime_format))
        except ValueError:
            print(f"Некорректная дата: {order_time_str}")
            continue

        if order_time < cutoff_time:
            continue
        if str(order["Status"]).strip().lower() == "ready":

            order_id = order["Order No"]
            order_items_for_order = [item for item in order_items if str(item["Order No"]).strip().lower() == str(order_id)]

            items = []
            user_name = get_user_name_from_current_users(users, order.get("Telephone No", "")) or "Unknown customer"
            for item in order_items_for_order:
                photo_url = ger_photo_url_by_name(item["Name"])
                try:
                    items.append({
                        "name": item["Name"],
                        "quantity": int(item["Quantity"]),
                        "amount": float(item["Amount"]),
                        "size": item.get("Size", ""),
                        "category": item.get("Category", ""),
                        "isGarlicCrust": str(item.get("isGarlicCrust", "")).strip().lower() == "true",
                        "isThinDough": str(item.get("isThinDough", "")).strip().lower() == "true",
                        "description": item.get("Description", ""),
                        "discount_amount": item.get("Sale Amount", 0),
                        "photo": photo_url,
                    })
                except Exception as e:
                    print(f"Ошибка при обработке item: {item}, {e}")

            history_orders.append({
                "orderId": order_id,
                "order_type": order.get("Type", ""),
                "amount_paid": float(order.get("Amount paid", 0)),
                "phone_number": order.get("Telephone No", ""),
                "sale_amount": float(order.get("Sale Amount", 0)),
                "customer_name": user_name,
                "order_created": order_time_str,
                "payment_type": order.get("Payment Type", ""),
                "notes": order.get("Notes", "Test note"),
                "items": items
            })
    logging.info(history_orders)
    return {"orders": history_orders}