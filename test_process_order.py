import json
from unittest.mock import MagicMock


def test_processes_order_and_publishes_notification(process_app, monkeypatch):
    table, sns = MagicMock(), MagicMock()
    table.update_item.side_effect = [
        {"Attributes": {"order_id": "o-1", "customer_email": "customer@example.com"}},
        {},
    ]
    monkeypatch.setattr(process_app, "_resources", lambda: (table, sns))
    monkeypatch.setenv("NOTIFICATIONS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:orders")
    event = {"Records": [{"messageId": "m-1", "body": json.dumps({"order_id": "o-1"})}]}

    result = process_app.lambda_handler(event, None)
    assert result == {"batchItemFailures": []}
    assert table.update_item.call_count == 2
    sns.publish.assert_called_once()


def test_reports_failed_message_for_retry(process_app, monkeypatch):
    table, sns = MagicMock(), MagicMock()
    table.update_item.side_effect = RuntimeError("temporary error")
    monkeypatch.setattr(process_app, "_resources", lambda: (table, sns))
    event = {"Records": [{"messageId": "m-2", "body": json.dumps({"order_id": "o-2"})}]}
    assert process_app.lambda_handler(event, None) == {
        "batchItemFailures": [{"itemIdentifier": "m-2"}]
    }

