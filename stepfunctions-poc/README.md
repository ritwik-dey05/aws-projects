Human Approval Workflow System using AWS Step Functions
This document outlines the components and implementation of a human approval workflow system built on AWS. The system uses Step Functions, Lambda, Aurora, SQS, and API Gateway to manage the approval process for question papers.

1. System Architecture
Here is a high-level overview of the system's architecture:

An API Gateway endpoint triggers a Lambda function to start the Step Function execution.

The "Create Request" Lambda saves the question details to a AuroraDB table and creates a corresponding task record.

The Step Function proceeds to the "Assign to Assessor" step, which sends a message with a task token to an SQS queue.

The SQS queue triggers a "Callback" Lambda. This Lambda stores the task token in the task record and sends an email notification to the assessor. The Step Function then pauses.

The assessor, prompted by the email, uses another API Gateway endpoint to submit their approval or rejection.

This triggers the "Resume Workflow" Lambda, which uses the stored task token to send the decision back to the paused Step Function.

The Step Function evaluates the decision in a Choice state.

Based on the choice, it transitions to a Success or Failed state, updating the task status in AuroraDB accordingly.

------------------------------------------------------------------------

Key Infrastructure Notes:

VPC: Both the Aurora Serverless database and the Lambda functions must reside within the same Amazon VPC to allow them to communicate securely.

AWS Secrets Manager: Database credentials should be stored securely in AWS Secrets Manager, not hardcoded in Lambda functions.

Lambda Layer: The Python Lambda functions will need the psycopg2 library to connect to PostgreSQL. This should be packaged as a Lambda Layer and attached to the functions.

2. Data Model and Database (Aurora Serverless PostgreSQL)
We will use two tables in our PostgreSQL database: questions and approval_tasks.

Table: questions
question_id (UUID, Primary Key): A unique identifier for the question.

question_text (TEXT): The text of the question.

options (JSONB): The multiple-choice answers, stored as a JSON array.

correct_answer (TEXT): The correct answer.

created_at (TIMESTAMPTZ): Timestamp of creation.

Table: approval_tasks
task_id (UUID, Primary Key): A unique identifier for the task.

question_id (UUID, Foreign Key): A reference to the questions table.

assigned_by (VARCHAR(255)): The email or ID of the person who created the request.

assigned_to (VARCHAR(255)): The email or ID of the assessor.

status (VARCHAR(50)): The current status of the task (e.g., PENDING, APPROVED, REJECTED).

task_token (TEXT): The token from the Step Function to resume the workflow.

comments (TEXT): Approval or rejection comments.

created_at (TIMESTAMPTZ): Timestamp of creation.

updated_at (TIMESTAMPTZ): Timestamp of the last update.

PostgreSQL DDL (Data Definition Language)
Here is the SQL script to create these tables.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the Questions table
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create the ApprovalTasks table
CREATE TABLE approval_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES questions(question_id),
    assigned_by VARCHAR(255) NOT NULL,
    assigned_to VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    task_token TEXT,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Optional: Create an index for faster lookups on question_id in the tasks table
CREATE INDEX idx_approval_tasks_question_id ON approval_tasks(question_id);

3. AWS Step Functions - ASL Definition
This ASL definition remains unchanged from the previous version, as the interface with the Lambda functions is consistent.
statemachine/approval_workflow.asl.json


4. AWS Lambda Functions (Python with psycopg2)
These functions are updated to connect to the Aurora PostgreSQL database. They fetch credentials from AWS Secrets Manager.
src/update_status/app.py
src/resume_workflow/app.py
src/create_request/app.py
src/callback/app.py

Helper Code: Database Connection
It's best practice to put connection logic in a separate file/layer. For simplicity, I'll include it as a helper function here.
psycopg2/app.py



--------------------------------------------------------------------------------

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

Local Development with AWS SAM
This guide explains how to use the AWS Serverless Application Model (SAM) CLI to build, test, and deploy the Human Approval Workflow application.

Project Structure
Your project should be structured as follows for the template.yaml to work correctly:

.
├── src
│   ├── create_request
│   │   └── app.py
│   ├── callback
│   │   └── app.py
│   ├── resume_workflow
│   │   └── app.py
│   └── update_status
│       └── app.py
├── statemachine
│   └── approval_workflow.asl.json
└── template.yaml

Prerequisites
AWS SAM CLI installed.

Docker installed and running (for local testing).

An existing infrastructure stack (VPC, DB, etc.) deployed via CloudFormation.

Development Steps
Step 1: Build Dependencies

The sam build command packages your application code and dependencies.

sam build --use-container

Step 2: Local Testing (Optional)

You can invoke your Lambda functions locally to test their logic. Note that testing functions requiring VPC resources (like a database connection) locally is complex and often requires mocking or connecting over a VPN.

To test a function that doesn't require VPC access:

# The event.json file contains the test payload for your function
sam local invoke CreateRequestFunction -e events/event.json

Step 3: Deploy the Application


