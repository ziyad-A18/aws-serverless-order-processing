import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.environ["ORDERS_TABLE"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
sns = boto3.client("sns")


def lambda_handler(event, context):
    failed_messages = []

    for record in event.get("Records", []):
        try:
            message = json.loads(record["body"])
            order_id = message["orderId"]
            processed_at = datetime.now(timezone.utc).isoformat()

            response = table.update_item(
                Key={"orderId": order_id},
                UpdateExpression=(
                    "SET #orderStatus = :completed, "
                    "processedAt = :processedAt"
                ),
                ConditionExpression="#orderStatus = :pending",
                ExpressionAttributeNames={"#orderStatus": "status"},
                ExpressionAttributeValues={
                    ":pending": "PENDING",
                    ":completed": "COMPLETED",
                    ":processedAt": processed_at,
                },
                ReturnValues="ALL_NEW",
            )

            order = response["Attributes"]

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"Order completed: {order_id}",
                Message=(
                    f"Order ID: {order_id}\n"
                    f"Customer: {order['customerName']}\n"
                    f"Items: {', '.join(order['items'])}\n"
                    f"Total: {order['total']}\n"
                    f"Status: {order['status']}"
                ),
            )

            print(f"Successfully processed order {order_id}")

        except ClientError as error:
            error_code = error.response["Error"]["Code"]

            if error_code == "ConditionalCheckFailedException":
                print(
                    "Order was already processed. "
                    f"Skipping duplicate message: {record['messageId']}"
                )
                continue

            print(f"AWS error: {error}")
            failed_messages.append({"itemIdentifier": record["messageId"]})

        except Exception as error:
            print(f"Processing failed: {error}")
            failed_messages.append({"itemIdentifier": record["messageId"]})

    return {"batchItemFailures": failed_messages}

