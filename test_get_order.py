import json
from decimal import Decimal
from unittest.mock import MagicMock


def test_get_existing_order(get_app, monkeypatch):
    table = MagicMock()
    table.get_item.return_value = {"Item": {"order_id": "o-1", "total": Decimal("12.50")}}
    resource = MagicMock()
    resource.Table.return_value = table
    monkeypatch.setattr(get_app.boto3, "resource", lambda service: resource)
    monkeypatch.setenv("ORDERS_TABLE", "orders")

    result = get_app.lambda_handler({"pathParameters": {"order_id": "o-1"}}, None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["total"] == 12.5


def test_get_missing_order_returns_404(get_app, monkeypatch):
    table = MagicMock()
    table.get_item.return_value = {}
    resource = MagicMock()
    resource.Table.return_value = table
    monkeypatch.setattr(get_app.boto3, "resource", lambda service: resource)
    monkeypatch.setenv("ORDERS_TABLE", "orders")
    result = get_app.lambda_handler({"pathParameters": {"order_id": "missing"}}, None)
    assert result["statusCode"] == 404

