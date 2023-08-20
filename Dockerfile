FROM python:3.11 AS cli

COPY ./cli/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

COPY ./cli /

ENTRYPOINT ["/usr/local/bin/python", "/main.py"]
CMD ["-h"]