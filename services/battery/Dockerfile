FROM python:3.11.6-alpine3.18

RUN pip install "python-socketio[client]" libmav

WORKDIR /app
COPY ./app.py app.py
COPY ./mavlink/message_definitions/v1.0/ mavlink/

CMD python3 ./app.py