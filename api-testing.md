# API testing

Set the deployed URL shown by `sam deploy`, without a trailing slash:

```bash
API_URL="https://example.execute-api.us-east-1.amazonaws.com/dev"
```

## Create an order

```bash
curl -i -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "items": [
      {"product_id": "AWS-BOOK-01", "quantity": 2, "unit_price": 29.99},
      {"product_id": "USB-CABLE-02", "quantity": 1, "unit_price": 9.50}
    ]
  }'
```

Expected initial response (`202 Accepted`):

```json
{
  "order_id": "generated-uuid",
  "status": "PENDING",
  "total": "69.48",
  "message": "Order accepted for asynchronous processing"
}
```

## Check the order status

Replace `generated-uuid` with the returned value:

```bash
curl "$API_URL/orders/generated-uuid"
```

SQS invokes the worker asynchronously, so the status progresses from `PENDING` to `PROCESSING` and then `COMPLETED`. A missing ID returns `404`.

## Run automated unit tests

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
pytest --cov=src --cov-report=term-missing
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

## Local SAM invocation

After `sam build`, invoke functions with the included sample events:

```bash
sam local invoke CreateOrderFunction --event events/create-order.json
sam local invoke GetOrderFunction --event events/get-order.json
sam local invoke ProcessOrderFunction --event events/sqs-order.json
```

The functions require the configured AWS resources and environment variables; unit tests are the quickest fully isolated local validation.

