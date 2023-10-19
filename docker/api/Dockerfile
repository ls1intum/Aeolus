FROM openjdk:22-slim as jar-builder

ADD bamboo-generator/ .
RUN ./gradlew shadowJar --no-daemon -x :generateJsonSchema2Pojo
RUN cp ./build/libs/bamboo-generator*-all.jar bamboo-generator.jar

FROM python:3.11-slim AS cli

RUN apt-get update && apt-get install -y default-jre git && rm -rf /var/cache

COPY --from=jar-builder /bamboo-generator.jar bamboo-generator.jar

COPY ../../api/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

COPY ../../cli/ /cli
WORKDIR /cli
RUN rm requirements.txt requirements.in

COPY ../../api /api
WORKDIR /api
RUN rm requirements.txt requirements.in

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]