# ============================================
# Victim Service Dockerfile
# Multi-stage build: Maven build -> JRE runtime
# ============================================

# Stage 1: Build
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /build
COPY pom.xml .
# Download dependencies first (Docker layer caching)
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

# Stage 2: Runtime
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Copy the built JAR
COPY --from=builder /build/target/*.jar app.jar

# Expose actuator port
EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]
