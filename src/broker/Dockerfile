FROM python:3.13.7-alpine3.21

WORKDIR /app

COPY broker /app

RUN pip install pyzmq

CMD ["python", "broker.py"]
