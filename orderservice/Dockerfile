# Use Amazon Corretto 17 as the base image
FROM amazoncorretto:17

# Set the maintainer label
LABEL maintainer="example@company.com"

# Set working directory
WORKDIR /app

# Copy the JAR file
COPY target/order-service-1.0.0.jar app.jar

# Expose port 8080
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# Run the application
ENTRYPOINT ["java", "-jar", "/app/app.jar"]