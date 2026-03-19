FROM python:3.13.7-alpine3.21

WORKDIR /app

RUN pip install --no-cache-dir pyzmq protobuf grpcio-tools

COPY common /app/common
COPY servidor /app

RUN python -m grpc_tools.protoc -I./common \
    --python_out=. \
    common/message.proto

CMD ["python", "servidor.py"]
