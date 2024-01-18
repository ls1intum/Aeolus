FROM docker.io/library/eclipse-temurin:17-jdk as jar-builder

ADD bamboo-generator/ .
RUN ./gradlew shadowJar --no-daemon -x :generateJsonSchema2Pojo
RUN cp ./build/libs/bamboo-generator*-all.jar bamboo-generator.jar

FROM python:3.11-slim AS cli

RUN apt-get update && apt-get install -y default-jre git && rm -rf /var/cache

COPY --from=jar-builder /bamboo-generator.jar /fastapi/api/bamboo-generator.jar

COPY ../../api/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

COPY ../../cli/ /fastapi/cli
WORKDIR /fastapi/cli
RUN rm requirements.txt requirements.in

COPY ../../api /fastapi/api
COPY schemas /fastapi/schemas
WORKDIR /fastapi/api
RUN rm requirements.txt requirements.in

EXPOSE 80

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
