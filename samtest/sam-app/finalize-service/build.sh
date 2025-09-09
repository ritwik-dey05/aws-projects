#!/bin/bash
mvn clean package -DskipTests
docker build -t finalize-service:latest .