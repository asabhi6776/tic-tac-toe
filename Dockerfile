FROM python:3.11-alpine3.15

LABEL maintainer="github.com/asabhi6776"


WORKDIR /code
COPY requirements.txt /code/requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /code/.

ENTRYPOINT [ "/bin/sh" ] 