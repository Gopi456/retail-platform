from flask import Flask, jsonify,request
import os
from app.database import get_db_connection
from app.customers import search_customers

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

@app.route("/customers/search")
def customer_search():
    search_term = request.args.get("q", "").strip()

    if not search_term:
        return jsonify({
            "error": "Search parameter 'q' is required"
        }), 400

    try:
        customers = search_customers(search_term)

        return jsonify({
            "count": len(customers),
            "customers": customers
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Customer search failed",
            "details": str(e)
        }), 500


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

@app.route("/db-health")
def db_health():
    try:
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "status": "UP",
            "database": "CONNECTED",
            "result": result[0]
        }), 200

    except Exception as e:
        return jsonify({
            "status": "DOWN",
            "database": "UNAVAILABLE",
            "error": str(e)
        }), 500

@app.route("/payment")
def payment():
    return jsonify({
        "payment_status": PAYMENT_STATUS,
        "message": "Payment processing is operating normally."
    })


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