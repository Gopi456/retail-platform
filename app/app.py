from flask import Flask, jsonify
import os

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "4.2.0")
PAYMENT_STATUS = os.getenv("PAYMENT_STATUS", "AVAILABLE")
FAIL_HEALTHCHECK = os.getenv("FAIL_HEALTHCHECK", "false").lower() == "true"


@app.route("/")
def home():
    return f"""
    <html>
        <head>
            <title>Retail Platform</title>
        </head>
        <body>
            <h1>Retail Platform</h1>
            <h2>Application Version: {VERSION}</h2>
            <p>Payment Status: {PAYMENT_STATUS}</p>
        </body>
    </html>
    """


@app.route("/health")
def health():
    if FAIL_HEALTHCHECK:
        return jsonify({
            "status": "DOWN",
            "version": VERSION
        }), 500

    return jsonify({
        "status": "UP",
        "version": VERSION
    }), 200


@app.route("/products")
def products():
    return jsonify({
        "products": [
            {
                "id": 1,
                "name": "Laptop",
                "price": 65000
            }
        ]
    })
@app.route("/orders")
def orders():
    return jsonify({
        "orders": [
            {
                "id": 1001,
                "status": "CONFIRMED"
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)