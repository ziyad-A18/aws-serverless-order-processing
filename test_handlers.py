import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).parents[1]


def load_handler(name, relative_path, env):
    with patch.dict(os.environ, env, clear=False), patch("boto3.resource") as resource, patch("boto3.client") as client:
        resource.return_value.Table.return_value = MagicMock()
        spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def test_create_order_rejects_empty_items():
    handler = load_handler(
        "create_order_test",
        "src/create_order/app.py",
        {"ORDERS_TABLE": "orders", "ORDERS_QUEUE_URL": "https://example.test/queue"},
    )
    result = handler.lambda_handler({"body": json.dumps({"customerId": "c1", "items": []})}, None)
    assert result["statusCode"] == 400


def test_create_order_accepts_valid_order():
    handler = load_handler(
        "create_order_valid_test",
        "src/create_order/app.py",
        {"ORDERS_TABLE": "orders", "ORDERS_QUEUE_URL": "https://example.test/queue"},
    )
    result = handler.lambda_handler(
        {"body": json.dumps({"customerId": "c1", "items": [{"productId": "p1", "quantity": 1}]})}, None
    )
    assert result["statusCode"] == 202
    handler.table.put_item.assert_called_once()
    handler.sqs.send_message.assert_called_once()


def test_process_order_reports_only_failed_records():
    handler = load_handler(
        "process_order_test",
        "src/process_order/app.py",
        {"ORDERS_TABLE": "orders", "ORDER_EVENTS_TOPIC_ARN": "arn:aws:sns:x:y:z"},
    )
    handler.process_record = MagicMock(side_effect=[None, RuntimeError("temporary")])
    event = {"Records": [{"messageId": "ok", "body": "{}"}, {"messageId": "bad", "body": "{}"}]}
    assert handler.lambda_handler(event, None) == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
