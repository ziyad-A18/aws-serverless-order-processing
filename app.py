import json
import logging
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _resources():
    table = boto3.resource("dynamodb").Table(os.environ["ORDERS_TABLE"])
    sns = boto3.client("sns")
    return table, sns


def process_record(record, table, sns):
    message = json.loads(record["body"])
    order_id = message["order_id"]
    now = datetime.now(timezone.utc).isoformat()

    try:
        result = table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #status = :processing, updated_at = :updated",
            ConditionExpression="#status = :pending",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":pending": "PENDING",
                ":processing": "PROCESSING",
                ":updated": now,
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            logger.info("Order was already processed", extra={"order_id": order_id})
            return
        raise

    order = result["Attributes"]
    completed_at = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET #status = :completed, updated_at = :updated, processed_at = :processed",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":completed": "COMPLETED",
            ":updated": completed_at,
            ":processed": completed_at,
        },
    )
    sns.publish(
        TopicArn=os.environ["NOTIFICATIONS_TOPIC_ARN"],
        Subject="Order completed",
        Message=json.dumps({
            "order_id": order_id,
            "customer_email": order["customer_email"],
            "status": "COMPLETED",
            "message": "Your order has been processed successfully.",
        }),
        MessageAttributes={
            "customer_email": {"DataType": "String", "StringValue": order["customer_email"]}
        },
    )
    logger.info("Order completed", extra={"order_id": order_id})


def lambda_handler(event, context):
    table, sns = _resources()
    failures = []
    for record in event.get("Records", []):
        try:
            process_record(record, table, sns)
        except Exception:
            logger.exception("Order processing failed")
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}

