#!/bin/bash

# Build and push Docker image
./build.sh

# Tag for ECR (replace with your ECR repository URI)
ECR_URI="327083199816.dkr.ecr.us-east-1.amazonaws.com/createrequest-service"
docker tag createrequest-service:latest $ECR_URI":latest"

# Push to ECR (uncomment after creating ECR repository)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI