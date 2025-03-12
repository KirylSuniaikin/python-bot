import logging
import uuid
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from app.models.models import MenuItem, OrderItem, Order, Customer, ExtraIngr, OrderTO

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_ID = "11tLnA8whcBHykGf8OmuOwmacbvons4BIHx7ZjvteNX0"
ORDERS_SHEET_ID = 36417195
ORDER_ITEMS_SHEET_ID = 447066114
MENU_ITEMS_SHEET_ID = 1153080402
CUSTOMERS_SHEET_ID = 821617987
EXTRA_INGR_SHEET_ID = 2019426420

creds = ""
#Credentials.from_service_account_file("google_sheets_cred.json", scopes=SCOPES))

client = gspread.authorize(creds)

menu_items_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(MENU_ITEMS_SHEET_ID)
orders_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(ORDERS_SHEET_ID)
order_items_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(ORDER_ITEMS_SHEET_ID)
customers_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(CUSTOMERS_SHEET_ID)
extra_ingr_sheet = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(EXTRA_INGR_SHEET_ID)


def save_user_name(phone_number, name):
    cell = customers_sheet.find(phone_number)
    if cell:
        customers_sheet.update_cell(cell.row, 3, name)


def update_user_info(order: Order):
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
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    customers_sheet.update(
        f"E{user_row_index}",
        [[new_orders_count, new_total_paid, current_date]]
    )

    logging.info(f"Updated user {order.telephone_no}: Orders={new_orders_count}, Amount Paid={new_total_paid}, Last Order={current_date}")


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
    logging.info(f"ID: {user_id}")
    for row in data:
        if str(row["ID"]).strip() == str(user_id).strip():
            logging.info(f"returning phone number: {row['Telephone No']}")
            return row["Telephone No"]
    return None


def get_user_name(phone_number):
    data = customers_sheet.get_all_records()
    for row in data:
        if str(row["Telephone No"]).strip() == str(phone_number).strip():
            return row["Name"]
    return None


def get_user_id(phone_number):
    data = customers_sheet.get_all_records()
    for row in data:
        if str(row["Telephone No"]).strip() == str(phone_number).strip():
            return row["ID"]
    return None


def add_new_user(phone_number):
    customer = Customer(
        id=str(uuid.uuid4())[:8],
        telephone_no=phone_number,
        name="",
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
        order.amount_paid
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
        item.description
    ])
