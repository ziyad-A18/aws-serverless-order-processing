# AWS resource cleanup

Deleting the CloudFormation stack removes the API, Lambda functions, IAM roles, queues, SNS topic, alarms, log configuration, and DynamoDB table created by this project.

```bash
sam delete --stack-name aws-serverless-order-processing
```

Confirm deletion:

```bash
aws cloudformation describe-stacks --stack-name aws-serverless-order-processing
```

AWS should return a stack-not-found validation error. Also check the deployment region for retained CloudWatch log groups and the SAM deployment S3 bucket if you want to remove build artifacts. Do not delete a shared SAM bucket if other applications use it.

The template intentionally sets the development DynamoDB table deletion policy to `Delete`. For production data, change both table policies to `Retain` before deployment and back up the table before cleanup.

