import json
from decimal import Decimal
from unittest.mock import MagicMock


def event(body):
    return {"body": json.dumps(body), "isBase64Encoded": False}


def test_create_order_returns_202(create_app, monkeypatch):
    table, sqs = MagicMock(), MagicMock()
    monkeypatch.setattr(create_app, "_resources", lambda: (table, sqs))
    monkeypatch.setenv("ORDERS_QUEUE_URL", "https://sqs.example/orders")

    result = create_app.lambda_handler(event({
        "customer_email": "Customer@Example.com",
        "items": [{"product_id": "P-1", "quantity": 2, "unit_price": 5.25}],
    }), None)

    body = json.loads(result["body"])
    assert result["statusCode"] == 202
    assert body["status"] == "PENDING"
    assert body["total"] == "10.50"
    assert table.put_item.call_args.kwargs["Item"]["total"] == Decimal("10.50")
    sqs.send_message.assert_called_once()


def test_rejects_invalid_email(create_app):
    result = create_app.lambda_handler(event({
        "customer_email": "invalid",
        "items": [{"product_id": "P-1", "quantity": 1, "unit_price": 1}],
    }), None)
    assert result["statusCode"] == 400


def test_rejects_empty_items(create_app):
    result = create_app.lambda_handler(event({
        "customer_email": "customer@example.com",
        "items": [],
    }), None)
    assert result["statusCode"] == 400

