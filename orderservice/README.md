# Spring Boot Order Service with ECS Fargate and API Gateway

This project demonstrates a complete AWS serverless infrastructure setup for deploying a Spring Boot application to ECS Fargate with an internal Application Load Balancer (ALB) and API Gateway integration using VPC Link.

## Architecture Overview

The solution includes:

1. **Spring Boot Application**: Simple REST API with GET `/order` endpoint returning JSON
2. **ECS Fargate**: Containerized deployment in private subnets
3. **Internal ALB**: Load balances traffic to Fargate containers
4. **API Gateway HTTP API**: Public endpoint with VPC Link to internal ALB
5. **Custom VPC**: Multi-AZ setup with public and private subnets
6. **Security Groups**: Proper network segmentation and access control

## Architecture Diagram

```
Internet → API Gateway → VPC Link → Internal ALB → ECS Fargate (Private Subnets)
                                        ↓
                                 Spring Boot App
                                   (Port 8080)
```

## Prerequisites

- AWS CLI installed and configured
- Docker installed
- Maven 3.6+ installed
- Java 17 installed
- ECR repository created

## Files Included

- `OrderServiceApplication.java` - Spring Boot application with `/order` endpoint
- `pom.xml` - Maven dependencies and build configuration
- `Dockerfile` - Container image definition
- `application.properties` - Spring Boot configuration
- `infrastructure.yaml` - Complete CloudFormation stack
- `build-and-deploy.sh` - Automated build and deployment script

## Quick Start

### Step 1: Build the Application

```bash
# Build the Spring Boot application
mvn clean package

# Verify the JAR was created
ls -la target/order-service-1.0.0.jar
```

### Step 2: Create ECR Repository

```bash
# Create ECR repository
aws ecr create-repository --repository-name order-service --region us-east-1

# Get login token and login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### Step 3: Build and Push Docker Image

```bash
# Build Docker image
docker build -t order-service:latest .

# Tag the image for ECR
docker tag order-service:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/order-service:latest

# Push to ECR
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/order-service:latest
```

### Step 4: Deploy Infrastructure

```bash
# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name order-service-infrastructure \
  --template-body file://infrastructure.yaml \
  --parameters ParameterKey=ECRImageURI,ParameterValue=<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/order-service:latest \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Monitor stack creation
aws cloudformation wait stack-create-complete --stack-name order-service-infrastructure --region us-east-1

# Get the API Gateway URL
aws cloudformation describe-stacks \
  --stack-name order-service-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`OrderServiceEndpoint`].OutputValue' \
  --output text \
  --region us-east-1
```

## Automated Deployment

Use the provided script for fully automated deployment:

```bash
# Make script executable
chmod +x build-and-deploy.sh

# Deploy everything
./build-and-deploy.sh

# Clean up resources when done
./build-and-deploy.sh cleanup
```

## Testing the Deployment

Once deployed, test the service using the API Gateway endpoint:

```bash
# Get the endpoint URL from CloudFormation outputs
ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name order-service-infrastructure \
  --query 'Stacks[0].Outputs[?OutputKey==`OrderServiceEndpoint`].OutputValue' \
  --output text \
  --region us-east-1)

# Test the /order endpoint
curl "$ENDPOINT"
```

Expected response:
```json
{
  "orderId": "ORDER-12345",
  "customerName": "John Doe",
  "productName": "Spring Boot Microservice",
  "quantity": 1,
  "price": 99.99,
  "status": "COMPLETED",
  "orderDate": "2025-08-16T12:19:00.123456",
  "message": "Order retrieved successfully from ECS Fargate service"
}
```

## Infrastructure Components

### VPC Configuration
- **CIDR**: 10.0.0.0/16
- **Public Subnets**: 10.0.0.0/24, 10.0.1.0/24 (for NAT Gateways)
- **Private Subnets**: 10.0.2.0/24, 10.0.3.0/24 (for ECS containers)

### Security Groups
1. **VPC Link SG**: Allows HTTP (80) from anywhere
2. **Internal ALB SG**: Allows HTTP (80) from VPC Link SG
3. **Container SG**: Allows HTTP (8080) from Internal ALB SG

### ECS Configuration
- **Launch Type**: Fargate
- **CPU**: 256 (0.25 vCPU)
- **Memory**: 512 MB
- **Desired Count**: 2 instances
- **Health Check**: `/actuator/health`

### Load Balancer
- **Type**: Application Load Balancer (Internal)
- **Listeners**: Port 80 → Target Group Port 8080
- **Health Check**: `/actuator/health`

### API Gateway
- **Type**: HTTP API
- **Integration**: HTTP_PROXY via VPC Link
- **Routes**: 
  - `GET /order` - Specific route
  - `ANY /{proxy+}` - Catch-all route

## Monitoring and Troubleshooting

### CloudWatch Logs
- **Log Group**: `/ecs/order-service`
- **Retention**: 7 days

### Health Checks
- **Container Health**: `http://localhost:8080/actuator/health`
- **ALB Health Check**: `/actuator/health` (30s interval)

### Common Issues

1. **VPC Link Not Ready**: Wait 5-10 minutes for VPC Link to become AVAILABLE
2. **503 Service Unavailable**: Check ECS service is running and healthy
3. **Security Group Issues**: Verify port 80 is allowed from VPC Link to ALB, and port 8080 from ALB to containers

## Cleanup

To remove all resources:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name order-service-infrastructure --region us-east-1

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name order-service-infrastructure --region us-east-1

# Delete ECR repository (optional)
aws ecr delete-repository --repository-name order-service --force --region us-east-1
```

## Security Considerations

- All application containers run in private subnets
- No direct internet access to containers
- ALB is internal-only, not accessible from internet
- API Gateway provides the only public entry point
- IAM roles follow least privilege principle
- Security groups implement proper network segmentation

## Cost Optimization

- Uses Fargate for serverless container management (no EC2 instances)
- CloudWatch log retention set to 7 days
- NAT Gateways are the main cost component (consider using VPC Endpoints for AWS services)

## Scaling

- **Horizontal**: Increase `DesiredCount` parameter
- **Vertical**: Adjust CPU/Memory in task definition
- **Auto Scaling**: Add Application Auto Scaling (not included in this template)

## Next Steps

1. Add Application Auto Scaling
2. Implement CI/CD pipeline
3. Add monitoring and alerting
4. Implement database connectivity
5. Add authentication/authorization
6. Configure custom domain for API Gateway

## Project Structure

```
.
├── OrderServiceApplication.java    # Spring Boot main application
├── pom.xml                        # Maven build configuration
├── Dockerfile                     # Container image definition
├── application.properties         # Spring Boot configuration
├── infrastructure.yaml            # CloudFormation template
├── build-and-deploy.sh           # Deployment automation script
└── README.md                     # This file
```

This solution provides a production-ready foundation for deploying Spring Boot microservices on AWS with proper security, scalability, and observability practices.
