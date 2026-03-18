FROM python:3.13.7-alpine3.21

WORKDIR /app

COPY . .

RUN pip install pyzmq

CMD ["python","servidor.py"]

FROM alpine:3.21

WORKDIR /app

RUN apk add --no-cache g++ make cmake zeromq-dev git

RUN git clone https://github.com/zeromq/cppzmq.git \
    && cp cppzmq/zmq.hpp /usr/include/

COPY . .

RUN g++ servidor.cpp -lzmq -o server

CMD ["./server"]
