FROM python:3.13.7-alpine3.21

WORKDIR /app

COPY proxy.py /app/

RUN pip install --no-cache-dir pyzmq

CMD ["python", "proxy.py"]
