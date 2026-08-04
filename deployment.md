# Deployment guide

## Prerequisites

- An AWS account with permission to deploy CloudFormation, Lambda, API Gateway, DynamoDB, SQS, SNS, IAM, and CloudWatch resources
- AWS CLI configured with `aws configure`
- AWS SAM CLI
- Python 3.12 for local tests

## Deploy

From the repository root:

```bash
sam validate --lint
sam build
sam deploy --guided
```

Suggested guided-deployment values:

- Stack name: `aws-serverless-order-processing`
- Region: your preferred AWS Region
- Parameter `Environment`: `dev`
- Parameter `NotificationEmail`: your email address, or leave blank
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

The deployment requires `CAPABILITY_NAMED_IAM` because the template creates explicit least-privilege Lambda roles. If an email was supplied, open the AWS SNS confirmation message and confirm the subscription.

## Obtain the API URL

```bash
aws cloudformation describe-stacks \
  --stack-name aws-serverless-order-processing \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text
```

Continue with [API testing](api-testing.md).

