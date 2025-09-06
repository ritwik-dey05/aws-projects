This document contains the complete Infrastructure as Code (IaC) setup for the Human Approval Workflow system using AWS CloudFormation and AWS SAM.

1. Best Practices and Recommendations
Before diving into the code, here are some best practices incorporated into this design and recommended for your implementation:

Separate Infrastructure and Application Stacks: As requested, we've split the CloudFormation into infrastructure.yaml and application.yaml. This is a crucial best practice. It protects your stable resources (like the database) from accidental changes during frequent application deployments.

Store Credentials in Secrets Manager: Database credentials are not hardcoded. They are created and stored in AWS Secrets Manager. Lambda functions are given IAM permission to read this specific secret at runtime.

Use a Lambda Layer for Dependencies: The psycopg2 library needed for PostgreSQL connection is best managed as a Lambda Layer. This keeps your function deployment packages small and makes dependency management easier. The templates below include the definition for this layer.

Principle of Least Privilege: The IAM roles are scoped with the minimum necessary permissions. For example, the Lambda role can only access the specific SQS queue and Secrets Manager secret it needs, not all of them in the account.

VPC for Security: All Lambda functions and the Aurora database are placed within a VPC. This ensures that they are not exposed to the public internet and can communicate securely. The database is in a private subnet, and the Lambdas are in an application subnet.

Use VPC Endpoints: For production environments, consider adding VPC Endpoints for S3, Secrets Manager, and SQS. This allows your Lambda functions to access these AWS services without their traffic leaving the AWS network, which is more secure and can reduce data transfer costs.

Parameterize Your Templates: Key configuration values like the database name are parameterized in the CloudFormation templates, making them reusable across different environments (e.g., dev, staging, prod).

2. CloudFormation - Infrastructure Stack
This template creates the VPC, subnets, Aurora Serverless database, Secrets Manager secret, and the SQS queue.

AWSTemplateFormatVersion: '2010-09-09'
Description: 'Infrastructure stack for the Human Approval Workflow: VPC, DB, SQS, Secrets'

Parameters:
  DBName:
    Type: String
    Default: 'ApprovalDB'
    Description: 'The name of the PostgreSQL database.'
  DBMasterUsername:
    Type: String
    Default: 'pgadmin'
    Description: 'The master username for the database.'

Resources:
  # ------------------------------------------------------------#
  # Networking
  # ------------------------------------------------------------#
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: '10.0.0.0/16'
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: 'ApprovalWorkflowVPC'

  AppSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: '10.0.1.0/24'
      AvailabilityZone: !Select [ 0, !GetAZs '' ]
      Tags:
        - Key: Name
          Value: 'AppSubnet1'

  DBSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: '10.0.10.0/24'
      AvailabilityZone: !Select [ 0, !GetAZs '' ]
      Tags:
        - Key: Name
          Value: 'DBSubnet1'

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  VPCGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  RouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  DefaultRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref RouteTable
      DestinationCidrBlock: '0.0.0.0/0'
      GatewayId: !Ref InternetGateway

  AppSubnet1RouteTableAssociation:
    Type: AWS::EC2::RouteTableAssociation
    Properties:
      SubnetId: !Ref AppSubnet1
      RouteTableId: !Ref RouteTable

  # ------------------------------------------------------------#
  # Security
  # ------------------------------------------------------------#
  LambdaSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: 'Security group for Lambda functions'
      VpcId: !Ref VPC
      SecurityGroupEgress:
        - IpProtocol: -1
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: 'LambdaSG'

  DBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: 'Security group for Aurora DB'
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: 'DbSG'

  DBIngressRule:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref DBSecurityGroup
      IpProtocol: 'tcp'
      FromPort: 5432
      ToPort: 5432
      SourceSecurityGroupId: !Ref LambdaSecurityGroup

  # ------------------------------------------------------------#
  # Database
  # ------------------------------------------------------------#
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: 'Subnet group for Aurora DB'
      SubnetIds:
        - !Ref DBSubnet1

  DBSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Description: 'Database credentials for the approval workflow'
      GenerateSecretString:
        SecretStringTemplate: !Sub '{"username": "${DBMasterUsername}"}'
        GenerateStringKey: 'password'
        PasswordLength: 16
        ExcludeCharacters: '"@/\'

  DBCluster:
    Type: AWS::RDS::DBCluster
    Properties:
      Engine: 'aurora-postgresql'
      EngineMode: 'provisioned' # serverless v2 is configured via ServerlessV2ScalingConfiguration
      DatabaseName: !Ref DBName
      MasterUsername: !GetAtt DBSecret.SecretValueFromJson.username
      MasterUserPassword: !GetAtt DBSecret.SecretValueFromJson.password
      DBSubnetGroupName: !Ref DBSubnetGroup
      VpcSecurityGroupIds:
        - !Ref DBSecurityGroup
      ServerlessV2ScalingConfiguration:
        MinCapacity: 0.5
        MaxCapacity: 2
      DeletionProtection: false # Set to true for production

  # ------------------------------------------------------------#
  # SQS Queue
  # ------------------------------------------------------------#
  ApprovalSqsQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: 'ApprovalSqsQueue'
      VisibilityTimeout: 90

Outputs:
  VpcId:
    Description: 'VPC ID'
    Value: !Ref VPC
  AppSubnetIds:
    Description: 'Application Subnet IDs'
    Value: !Ref AppSubnet1
  LambdaSecurityGroupId:
    Description: 'Security Group ID for Lambda Functions'
    Value: !Ref LambdaSecurityGroup
  DBSecretArn:
    Description: 'ARN of the Secrets Manager secret for DB credentials'
    Value: !Ref DBSecret
  ApprovalSqsQueueUrl:
    Description: 'URL of the SQS queue'
    Value: !Ref ApprovalSqsQueue
  ApprovalSqsQueueArn:
    Description: 'ARN of the SQS queue'
    Value: !GetAtt ApprovalSqsQueue.Arn
