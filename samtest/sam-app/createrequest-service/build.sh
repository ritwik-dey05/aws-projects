#!/bin/bash
mvn clean package -DskipTests
docker build -t createrequest-service .
echo "CreateRequest service built successfully"