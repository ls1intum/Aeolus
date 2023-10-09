FROM ubuntu:22.04 as cli-worker

RUN apt update && apt install -y curl wget git

WORKDIR /workdir

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]