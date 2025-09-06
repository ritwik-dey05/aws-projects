Deploying the Human Approval Workflow with AWS CloudFormation
This guide explains how to deploy the application using the two-stack CloudFormation approach.

Prerequisites
AWS CLI installed and configured with appropriate permissions.

A verified email address in Amazon SES to use as the sender.

Deployment Steps
Step 1: Package Lambda Code

For a real deployment, you would package your Python code and its dependencies into ZIP files and upload them to an S3 bucket. For this example, the code is inlined in application.yaml.

Step 2: Deploy the Infrastructure Stack

This stack creates the VPC, database, SQS queue, and secrets. You only need to do this once per environment.

aws cloudformation deploy \
    --template-file infra-cloudformation.yaml \
    --stack-name ApprovalWorkflow-Infrastructure \
    --parameter-overrides DBMasterUsername=myadmin \
    --capabilities CAPABILITY_IAM

Step 3: Deploy the Application Stack

This stack creates the Lambdas, API Gateway, and Step Function. It uses the outputs from the infrastructure stack as its inputs.

First, retrieve the outputs from the infrastructure stack:

aws cloudformation describe-stacks --stack-name ApprovalWorkflow-Infrastructure --query "Stacks[0].Outputs"

Now, use those output values to deploy the application stack.

# Replace the parameter values with the outputs from the previous command
aws cloudformation deploy \
    --template-file application-cloudformation.yaml \
    --stack-name ApprovalWorkflow-Application \
    --parameter-overrides \
        VpcId=vpc-xxxxxxxxxxxx \
        AppSubnetIds=subnet-xxxxxxxxxxxx \
        LambdaSecurityGroupId=sg-xxxxxxxxxxxx \
        DBSecretArn=arn:aws:secretsmanager:..... \
        ApprovalSqsQueueUrl=https://sqs..... \
        ApprovalSqsQueueArn=arn:aws:sqs:..... \
    --capabilities CAPABILITY_IAM

After deployment, the API Gateway endpoint URL will be available in the outputs of the ApprovalWorkflow-Application stack.

Updating the Application
To update your Lambda function code or the state machine definition, simply modify the application.yaml template and re-run the aws cloudformation deploy command for the ApprovalWorkflow-Application stack. The infrastructure stack remains untouched.