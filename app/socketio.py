import logging
import threading
from flask_socketio import SocketIO, join_room

socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")


@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on("join_room")
def handle_join_room(room_name):
    join_room(room_name)
    from flask import request
    print(f"✅ Client joined room: {room_name}")
    print(f"Client sid: {request.sid}")
    print(f"All sids in room {room_name}: {socketio.server.manager.rooms['/'].get(room_name, set())}")


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")


def emit_order_created(order_data: dict):
    room_participants = list(socketio.server.manager.rooms['/'].get('orders_room', set()))
    print(f"🔔 Clients in 'orders_room': {room_participants}")
    ack_received = {"status": False}

    def ack(response):
        ack_received["status"] = True
        print(f"✅ Client acknowledged: {response}")

    try:
        socketio.emit('order_created', order_data, callback=ack, room="orders_room")
        print("ℹ️ Emitted with ACK, waiting for client response...")

        def check_ack():
            if not ack_received["status"]:
                print("⚠️ No ACK received after 3 seconds. Resending...")
                socketio.emit('order_created', order_data, callback=ack, room="orders_room")

        threading.Timer(3.0, check_ack).start()

    except Exception as e:
        logging.error(f"❌ order_created error: {e}")

def emit():
    print(f"✅ Client acknowledged:")
    socketio.emit('test_push', "hello")


def emit_order_updated(order_data):
    try:
        socketio.emit('order_updated', order_data)
    except Exception as e:
        logging.error(f"❌ order_update error: {e}")
