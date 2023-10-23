FROM openjdk:22-slim as jar-builder

ADD bamboo-generator/ .
RUN ./gradlew shadowJar --no-daemon -x :generateJsonSchema2Pojo
RUN cp ./build/libs/bamboo-generator*-all.jar bamboo-generator.jar

FROM python:3.11-slim AS cli

RUN apt-get update && apt-get install -y default-jre git && rm -rf /var/cache

COPY --from=jar-builder /bamboo-generator.jar bamboo-generator.jar

COPY ../../cli/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

COPY ../../cli /
RUN rm requirements.txt requirements.in
RUN ln -s /main.py /usr/local/bin/aeolus && chmod +x /usr/local/bin/aeolus

ENTRYPOINT ["aeolus"]
CMD ["-h"]