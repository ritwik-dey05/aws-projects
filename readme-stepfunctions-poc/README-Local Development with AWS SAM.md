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

Deploy your serverless application to AWS. The first time you deploy, use the --guided flag to specify parameters and save them to a samconfig.toml file.

# Run this the first time
sam deploy --guided

# For subsequent deployments
sam deploy

The guided deployment will prompt you for the parameters defined in template.yaml (VPC IDs, Secret ARN, etc.). You will get these values from the outputs of your CloudFormation infrastructure stack.

SAM Limitations
What SAM Excels At: SAM is designed to simplify the definition and deployment of serverless resources like Lambda, API Gateway, and Step Functions. Its CLI provides powerful tools for local testing and packaging of these components.

What SAM Doesn't Natively Manage: The following components from our architecture are not created using SAM and are considered part of the underlying infrastructure that the serverless application depends on:

VPC, Subnets, Security Groups: While you can define these using standard CloudFormation syntax within a SAM template, it's not the primary use case. These are typically managed by a separate infrastructure team or CloudFormation stack.

Aurora Serverless Database (RDS): SAM has no special resource type (AWS::Serverless::...) for databases. It must be defined with the standard AWS::RDS::DBCluster resource, which again is better handled in a dedicated infrastructure stack.

AWS Secrets Manager Secret: This is also a foundational resource that is defined using the standard AWS::SecretsManager::Secret resource type.

The best practice is to let SAM manage the application code and its direct event sources, while CloudFormation manages the stable, foundational infrastructure.