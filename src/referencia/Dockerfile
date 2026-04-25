FROM python:3.13.7-alpine3.21

WORKDIR /app

RUN pip install --no-cache-dir pyzmq

COPY referencia.py /app/

CMD ["python", "-u", "referencia.py"]
