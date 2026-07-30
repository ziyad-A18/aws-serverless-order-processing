import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import boto3


TABLE_NAME = os.environ["ORDERS_TABLE"]
QUEUE_URL = os.environ["QUEUE_URL"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
sqs = boto3.client("sqs")


def api_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    try:
        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        customer_name = body.get("customerName")
        items = body.get("items")
        total = body.get("total")

        if not isinstance(customer_name, str) or not customer_name.strip():
            return api_response(400, {"error": "customerName is required"})

        if (
            not isinstance(items, list)
            or not items
            or not all(isinstance(item, str) for item in items)
        ):
            return api_response(
                400,
                {"error": "items must be a non-empty list of product names"},
            )

        try:
            total_decimal = Decimal(str(total))
        except (InvalidOperation, TypeError, ValueError):
            return api_response(400, {"error": "total must be a valid number"})

        if total_decimal <= 0:
            return api_response(400, {"error": "total must be greater than zero"})

        order_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        table.put_item(
            Item={
                "orderId": order_id,
                "customerName": customer_name.strip(),
                "items": items,
                "total": total_decimal,
                "status": "PENDING",
                "createdAt": created_at,
            },
            ConditionExpression="attribute_not_exists(orderId)",
        )

        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({"orderId": order_id}),
        )

        return api_response(
            201,
            {
                "message": "Order created",
                "orderId": order_id,
                "status": "PENDING",
            },
        )

    except Exception as error:
        print(f"Create order failed: {error}")
        return api_response(500, {"error": "Internal server error"})

