import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
table = dynamodb.Table(os.environ["ORDERS_TABLE"])
topic_arn = os.environ["ORDER_EVENTS_TOPIC_ARN"]


def process_record(record):
    message = json.loads(record["body"])
    order_id = message["orderId"]
    processed_at = datetime.now(timezone.utc).isoformat()

    result = table.update_item(
        Key={"orderId": order_id},
        UpdateExpression="SET #status = :processed, processedAt = :processed_at",
        ConditionExpression="attribute_exists(orderId) AND #status = :pending",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":pending": "PENDING",
            ":processed": "PROCESSED",
            ":processed_at": processed_at,
        },
        ReturnValues="ALL_NEW",
    )

    sns.publish(
        TopicArn=topic_arn,
        Subject="Order processed",
        Message=json.dumps(
            {"eventType": "ORDER_PROCESSED", "order": result["Attributes"]},
            default=str,
        ),
    )


def lambda_handler(event, context):
    failures = []
    for record in event.get("Records", []):
        try:
            process_record(record)
        except Exception as error:
            error_code = getattr(error, "response", {}).get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                # A duplicate delivery or a missing order needs no retry.
                print(json.dumps({"level": "INFO", "message": "Order already handled or missing"}))
                continue
            print(json.dumps({"level": "ERROR", "message": str(error), "messageId": record.get("messageId")}))
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
