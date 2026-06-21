import threading
from flask import Flask
import config

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def run():
    app.run(host="0.0.0.0", port=config.PORT)


def keep_alive():
    t = threading.Thread(target=run, daemon=True)
    t.start()
