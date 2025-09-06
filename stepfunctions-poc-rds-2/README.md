# Human Approval Workflow (POC) — RDS + Step Functions

- Aurora → **RDS for PostgreSQL** (lower cost for POC).
- **ASL externalized**: `sam/statemachine/approval_workflow.asl.json` referenced by SAM via `DefinitionUri`.
- **Strict DB ingress**: **Lambda SG ➜ DB SG** (no CIDR).
- **Email**: default via SNS topic; optional SES SMTP.

## Repo layout
- `cfn/static-infra.yaml` — VPC, subnets, RDS, Secrets, SQS (+DLQ), SNS, VPC endpoints (SecretsMgr/SQS/SNS).
- `sam/template.yaml` — HTTP API, Lambdas, Step Functions, SQS event source; adds **SG ingress** from Lambda SG to DB SG.
- `src/*` — Lambda handlers.
- `db/schema.sql` — PostgreSQL DDL.
- `events/*.json` — local test payloads.
- `requirements.txt` — deps.

## Step-by-step (POC)

1. **Deploy static infra**:
   ```bash
   aws cloudformation deploy      --stack-name approval-static      --template-file cfn/static-infra.yaml      --capabilities CAPABILITY_NAMED_IAM      --parameter-overrides DBPassword='REPLACE_ME'
   ```
   **Deploy bastion host
   ```bash
   aws cloudformation deploy \
  --stack-name approval-bastion \
  --template-file cfn/ssm-bastion.yaml \
  --capabilities CAPABILITY_NAMED_IAM
  ```

2. **Initialize DB schema**:
   ```bash
   psql "host=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbHost'].Value" --output text)          port=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbPort'].Value" --output text)          dbname=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbName'].Value" --output text)          user=appuser password='REPLACE_ME'"      -f db/schema.sql
   ```

   2.1 Running postgers client locally - On a different terminal
   ```bash
   DB_INSTANCE_ID=$(aws cloudformation describe-stacks --stack-name approval-bastion \
   --query "Stacks[0].Outputs[?OutputKey=='BastionInstanceId'].OutputValue" --output text)

   RDS_HOST=$(aws cloudformation list-exports \
   --query "Exports[?Name=='ApprovalDbHost'].Value" --output text)

   aws ssm start-session \
   --target "$DB_INSTANCE_ID" \
   --document-name AWS-StartPortForwardingSessionToRemoteHost \
   --parameters "{\"host\":[\"$RDS_HOST\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"5432\"]}"

   psql -h 127.0.0.1 -p 5432 -U appuser -d appdb -f db/schema.sql

   psql -h 127.0.0.1 -p 5432 -U appuser -d appdb -f db/sample-data.sql
   ```

3. **Deploy dynamic app** (enforces **Lambda SG ➜ DB SG**):
   ```bash
   aws cloudformation delete-stack --stack-name approval-app
   aws cloudformation wait stack-delete-complete --stack-name approval-app

   sam build --use-container -t sam/template.yaml

  sam deploy \
  --stack-name approval-app \
  --template-file sam/template.yaml \
  --region $REGION \
  --s3-bucket $BUCKET \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    VpcId=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalVpcId'].Value" --output text) \
    PrivateSubnetIds=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalPrivateSubnets'].Value" --output text) \
    DbSecretArn=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbSecretArn'].Value" --output text) \
    DbHost=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbHost'].Value" --output text) \
    DbPort=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbPort'].Value" --output text) \
    DbName=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbName'].Value" --output text) \
    ApprovalQueueUrl=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalQueueUrl'].Value" --output text) \
    ApprovalQueueArn=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalQueueArn'].Value" --output text) \
    EmailTopicArn=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalEmailTopicArn'].Value" --output text) \
    DbSecurityGroupId=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbSecurityGroupId'].Value" --output text)

   ```

4. **Subscribe approver email** (optional):
   ```bash
   TOPIC=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalEmailTopicArn'].Value" --output text)
   aws sns subscribe --topic-arn "$TOPIC" --protocol email --notification-endpoint your.email@example.com
   ```

5. **Test**:
   ```bash
   API=$(aws cloudformation describe-stacks --stack-name approval-app --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)

   # Create
   curl -sS -X POST "$API/requests" -H "Content-Type: application/json"      -d '{"title":"Midterm QP","content":"Set A, Physics","assessorEmail":"your.email@example.com"}'

   # Approve/Reject via email link (GET) or programmatically:
   curl -sS -X POST "$API/requests/<taskId>/decision" -H "Content-Type: application/json"      -d '{"decision":"APPROVE","comments":"ok"}'
   ```

6. **Clean up**:
   ```bash
   sam delete --stack-name approval-app
   aws cloudformation delete-stack --stack-name approval-static
   ```

## Notes
- No NAT; VPC **Interface Endpoints** used for Secrets/SQS/SNS.
- If you need SES API instead of SMTP/SNS, expect NAT or an HTTP egress path.
- Add CloudWatch alarms for DLQ depth, Lambda errors, SFN failures for production.

7. **Create ECR Repository:
```bash 
aws ecr create-repository --repository-name callback-service --region us-east-1
```
8. Build and Push Image
```bash
cd callback-service
./build.sh

# Get ECR login token and push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/callback-service:latest
```

9. Deploy ECS Service:
```bash
aws cloudformation deploy \
  --template-file ecs-services.yaml \
  --stack-name ecs-services \
  --parameter-overrides \
    VpcId=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalVpcId'].Value" --output text) \
    PrivateSubnetIds=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalPrivateSubnets'].Value" --output text) \
    ECSClusterName=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalECSClusterName'].Value" --output text) \
    ECSSecurityGroupId=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalECSSecurityGroupId'].Value" --output text) \
    DbSecretArn=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbSecretArn'].Value" --output text) \
    DbHost=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbHost'].Value" --output text) \
    DbPort=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbPort'].Value" --output text) \
    DbName=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalDbName'].Value" --output text) \
    ApprovalQueueUrl=$(aws cloudformation list-exports --query "Exports[?Name=='ApprovalQueueUrl'].Value" --output text) \
    AppBaseUrl="https://$(aws cloudformation describe-stacks --stack-name sam-app --query 'Stacks[0].Outputs[?OutputKey==`WorkflowApi`].OutputValue' --output text)" \
    CallbackServiceImageUri="<IMAGE_URI>" \
  --capabilities CAPABILITY_IAM

```

10. Get Parameters from Static Stack
aws cloudformation describe-stacks --stack-name static-infra --query 'Stacks[0].Outputs'


11. Redeploy SAM Template
sam deploy --parameter-overrides $(cat samconfig.toml parameters)

The ECS service will start polling the SQS queue and processing messages instead of the Lambda function.

**What to do if i need to rebuild the ecs service ?

1. Build and Push New Image
cd callback-service
./build.sh

# Push to ECR with same tag
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/callback-consumer:latest


bash
2. Force ECS Service Update
# Force new deployment to pull latest image
aws ecs update-service \
  --cluster approval-cluster \
  --service callback-service \
  --force-new-deployment


bash
What happens:

ECS will stop old tasks and start new ones with the updated image

Same task definition, same configuration

Only the container image changes

Zero downtime deployment

Alternative: Use image tags with versions (recommended for production):

docker tag callback-service:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/callback-service:v1.1
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/callback-service:v1.1

# Update stack with new image URI
aws cloudformation deploy --template-file ecs-services.yaml --stack-name ecs-services --parameter-overrides CallbackServiceImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/callback-service:v1.1 [other params]


bash