#!/bin/bash

# Build and Deploy Script for Spring Boot Order Service
# This script automates the entire build and deployment process

set -e  # Exit on any error

# Configuration
STACK_NAME="order-service-infrastructure"
REGION="us-east-1"
REPOSITORY_NAME="order-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi

    # Check Maven
    if ! command -v mvn &> /dev/null; then
        print_error "Maven is not installed. Please install it first."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi

    print_success "All prerequisites are met"
}

# Function to get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text 2>/dev/null || {
        print_error "Failed to get AWS account ID. Please check your AWS credentials."
        exit 1
    }
}

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local account_id=$1
    print_status "Creating ECR repository if it doesn't exist..."

    if aws ecr describe-repositories --repository-names "$REPOSITORY_NAME" --region "$REGION" &> /dev/null; then
        print_warning "ECR repository '$REPOSITORY_NAME' already exists"
    else
        aws ecr create-repository \
            --repository-name "$REPOSITORY_NAME" \
            --region "$REGION" > /dev/null
        print_success "ECR repository '$REPOSITORY_NAME' created"
    fi
}

# Function to build Spring Boot application
build_application() {
    print_status "Building Spring Boot application..."
    mvn clean package -q

    if [ -f "target/order-service-1.0.0.jar" ]; then
        print_success "Spring Boot application built successfully"
    else
        print_error "Failed to build Spring Boot application"
        exit 1
    fi
}

# Function to build and push Docker image
build_and_push_image() {
    local account_id=$1
    local image_uri="${account_id}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:latest"

    print_status "Building Docker image..."
    docker build -t "$REPOSITORY_NAME:latest" . -q

    print_status "Tagging Docker image for ECR..."
    docker tag "$REPOSITORY_NAME:latest" "$image_uri"

    print_status "Logging into ECR..."
    aws ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin "${account_id}.dkr.ecr.${REGION}.amazonaws.com" > /dev/null

    print_status "Pushing Docker image to ECR..."
    docker push "$image_uri" > /dev/null

    print_success "Docker image pushed successfully"
    echo "$image_uri"
}

# Function to deploy CloudFormation stack
deploy_infrastructure() {
    local image_uri=$1

    print_status "Deploying CloudFormation stack..."

    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        print_warning "Stack '$STACK_NAME' already exists. Updating..."
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://infrastructure.yaml \
            --parameters ParameterKey=ECRImageURI,ParameterValue="$image_uri" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION" > /dev/null

        print_status "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
    else
        print_status "Creating new stack '$STACK_NAME'..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body file://infrastructure.yaml \
            --parameters ParameterKey=ECRImageURI,ParameterValue="$image_uri" \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION" > /dev/null

        print_status "Waiting for stack creation to complete (this may take 10-15 minutes)..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$STACK_NAME" \
            --region "$REGION"
    fi

    print_success "Infrastructure deployed successfully"
}

# Function to get and display outputs
show_outputs() {
    print_status "Retrieving deployment information..."

    # Get stack outputs
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output json)

    echo
    print_success "=== DEPLOYMENT SUCCESSFUL ==="
    echo

    # Extract specific outputs
    local api_endpoint=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="OrderServiceEndpoint") | .OutputValue')
    local api_base_url=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="ApiGatewayInvokeURL") | .OutputValue')
    local vpc_id=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="VPCId") | .OutputValue')
    local cluster_name=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="ECSClusterName") | .OutputValue')

    echo "🚀 Order Service Endpoint: $api_endpoint"
    echo "🌐 API Gateway Base URL: $api_base_url"
    echo "🏗️  VPC ID: $vpc_id"
    echo "⚙️  ECS Cluster: $cluster_name"
    echo

    print_status "Testing the deployment..."
    echo "curl \"$api_endpoint\""
    echo

    # Test the endpoint
    if curl -s -f "$api_endpoint" > /dev/null; then
        print_success "✅ Service is responding successfully!"
        echo
        echo "Sample response:"
        curl -s "$api_endpoint" | jq '.' || curl -s "$api_endpoint"
    else
        print_warning "⚠️  Service might still be starting up. Try the endpoint in a few minutes."
    fi

    echo
    echo "📝 To monitor your deployment:"
    echo "   - CloudFormation: https://${REGION}.console.aws.amazon.com/cloudformation/home?region=${REGION}#/stacks"
    echo "   - ECS Cluster: https://${REGION}.console.aws.amazon.com/ecs/home?region=${REGION}#/clusters"
    echo "   - API Gateway: https://${REGION}.console.aws.amazon.com/apigateway/main/apis?region=${REGION}"
}

# Function to clean up resources
cleanup() {
    print_warning "Cleaning up resources..."

    print_status "Deleting CloudFormation stack..."
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"

    print_status "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"

    print_status "Deleting ECR repository..."
    aws ecr delete-repository \
        --repository-name "$REPOSITORY_NAME" \
        --force \
        --region "$REGION" > /dev/null

    print_success "Cleanup completed"
}

# Main execution
main() {
    echo "🚀 Spring Boot Order Service - Build and Deploy Script"
    echo "================================================="

    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites

            account_id=$(get_account_id)
            print_success "Using AWS Account: $account_id"

            create_ecr_repo "$account_id"
            build_application
            image_uri=$(build_and_push_image "$account_id")
            deploy_infrastructure "$image_uri"
            show_outputs
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  deploy   - Build and deploy the application (default)"
            echo "  cleanup  - Remove all AWS resources"
            echo "  help     - Show this help message"
            echo
            exit 0
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run the main function with all arguments
main "$@" 