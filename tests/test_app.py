import os


os.environ["APP_VERSION"] = "4.2.0"
os.environ["PAYMENT_STATUS"] = "AVAILABLE"
os.environ["FAIL_HEALTHCHECK"] = "false"

from app.app import app
from unittest.mock import patch



def test_home():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Retail Platform" in response.data


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "UP"
    assert response.json["environment"] == "DEV"

def test_customer_search_missing_query():
    client = app.test_client()

    response = client.get("/customers/search")

    assert response.status_code == 400
    assert response.json["error"] == "Search parameter 'q' is required"


@patch("app.app.search_customers")
def test_customer_search(mock_search_customers):
    mock_search_customers.return_value = [
        {
            "id": 1,
            "name": "Gopi Reddy",
            "email": "gopi@example.com"
        }
    ]

    client = app.test_client()

    response = client.get("/customers/search?q=Gopi")

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert response.json["customers"][0]["name"] == "Gopi Reddy"

    mock_search_customers.assert_called_once_with("Gopi")