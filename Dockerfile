FROM python:3.10-alpine

COPY . /app
WORKDIR /app

RUN apk add --no-cache ffmpeg
RUN pip install -r requirements.txt

CMD ["python", "/app/src/main.py"]
