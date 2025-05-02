import logging

from flask_socketio import SocketIO


socketio = SocketIO(cors_allowed_origins="*")


@socketio.on('connect')
def handle_connect():
    print("Client connected")


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")


def emit_order_created(order_data: dict):
    try:
        socketio.emit('order_created', order_data)
    except Exception as e:
        logging.error(f"❌ order_created error: {e}")


def emit_order_updated(order_data):
    try:
        socketio.emit('order_updated', order_data)
    except Exception as e:
        logging.error(f"❌ order_update error: {e}")
