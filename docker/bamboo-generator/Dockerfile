FROM openjdk:17-slim as jar-builder

ADD bamboo-generator/ .
RUN ./gradlew shadowJar --no-daemon -x :generateJsonSchema2Pojo
RUN cp ./build/libs/bamboo-generator*-all.jar bamboo-generator.jar

FROM openjdk:17-slim as runtime

COPY --from=jar-builder /bamboo-generator.jar bamboo-generator.jar
EXPOSE 8091
ENTRYPOINT ["java", "-jar", "bamboo-generator.jar"]