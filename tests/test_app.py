import os

os.environ["APP_VERSION"] = "4.2.0"
os.environ["PAYMENT_STATUS"] = "AVAILABLE"
os.environ["FAIL_HEALTHCHECK"] = "false"

from app.app import app


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