FROM eclipse-temurin:21.0.8_9-jre-jammy

WORKDIR /app

COPY target/callback-consumer-*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]