FROM python:3.9.0b3-alpine3.12

ENV mongo='mongodb+srv://goshiz:goshiz@cluster0-fx7lq.mongodb.net/<dbname>?retryWrites=true&w=majority'
ENV dbname='haven_stagenet'
ENV daemon_url='http://host.docker.internal:37750'
RUN apk add build-base supervisor 

RUN pip install requests pymongo dnspython falcon falcon_cors falcon-marshmallow falcon_apispec gunicorn python-dateutil

RUN mkdir /src
WORKDIR /src

COPY . /src
