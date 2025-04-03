import logging

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from googleapiclient.http import MediaFileUpload
from app.google_sheets import drive_service, save_check_link, get_order_data


def generate_pdf(order_id, folder_id="1CCrcR8Tdh41_FZ0ozAUJvvuOtM4oUqbj"):
    order_data = get_order_data(order_id)
    pdf_filename = f"{order_data.order_id}.pdf"
    pdf_path = f"/tmp/{pdf_filename}"

    if not order_data:
        logging.error(f"Order data not found for order_id: {order_id}")
        return None
    logging.info(f"No problems there")

    try:
        logging.info(f"Creating PDF file at {pdf_path}")

        c = canvas.Canvas(pdf_path, pagesize=letter)
        logging.info("Canvas initialized successfully")

        c.drawString(100, 750, f"Order Receipt - {order_data.order_id}")
        logging.info("Draw order ID")

        c.drawString(100, 690, f"Total: {order_data.total} BHD")
        logging.info("Draw total")

        c.drawString(100, 670, f"Date: {order_data.date}")
        logging.info("Draw date")

        y_position = 650
        for item in order_data.items:
            c.drawString(100, y_position, f"{item.name} - {item.amount} BHD")
            logging.info(f"Draw item: {item.name}, amount: {item.amount}")
            y_position -= 20

        c.save()
        logging.info("PDF successfully saved.")

    except Exception as e:
        logging.error(f"Error while creating PDF: {e}")
        return None

    logging.info("PDF successfully saved.")

    query = f"name='{pdf_filename}' and '{folder_id}' in parents and trashed=false"
    existing_files = drive_service.files().list(q=query, fields="files(id)").execute()
    file_list = existing_files.get("files", [])

    if file_list:
        existing_file_id = file_list[0]["id"]
        logging.info(f"Existing file found: {existing_file_id}, updating it.")
        drive_service.files().delete(fileId=existing_file_id).execute()

    file_metadata = {
        "name": pdf_filename,
        "parents": [folder_id]
    }

    media = MediaFileUpload(pdf_path, mimetype="application/pdf")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    file_id = file.get("id")
    file_link = f"https://drive.google.com/file/d/{file_id}/view"
    logging.info(f"Check PDF generated: {file_link}")

    save_check_link(order_data.order_id, file_link)
    return file_link
