FROM debian:bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    g++ \
    libzmq3-dev \
    libprotobuf-dev \
    protobuf-compiler \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -o /usr/include/zmq.hpp \
    https://raw.githubusercontent.com/zeromq/cppzmq/master/zmq.hpp

COPY common /app/common
COPY cliente /app

RUN protoc --proto_path=common --cpp_out=. common/message.proto
RUN g++ cliente.cpp message.pb.cc -I. $(pkg-config --cflags --libs protobuf) -lzmq -lpthread -o cliente

FROM debian:bookworm-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    libzmq5 \
    libprotobuf32 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/cliente .

CMD ["./cliente"]
