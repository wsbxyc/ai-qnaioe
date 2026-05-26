FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/tech-assistant-system-1.0.0.jar app.jar
EXPOSE 8080
ENV JAVA_OPTS=""
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
