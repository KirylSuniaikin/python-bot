import logging
from app import create_app
from app.socketio import socketio

app = create_app()

if __name__ == "__main__":
    logging.info("Flask app started")
    socketio.run(
        app,
        host='0.0.0.0',
        port=8000,
        allow_unsafe_werkzeug=True
    )