#!/bin/bash

# Build and deploy Spring Boot service to ECS

# Build the application
mvn clean package -DskipTests

# Build Docker image
docker build -t callback-service .

# Tag for ECR (replace with your ECR repository URI)
ECR_URI="327083199816.dkr.ecr.us-east-1.amazonaws.com/callback-service"
docker tag callback-service:latest $ECR_URI:latest

# Push to ECR (uncomment after creating ECR repository)
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
# docker push $ECR_URI:latest

echo "Build complete. Update ImageUri parameter in callback-service.yaml with: $ECR_URI:latest"