FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg git && apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV WHISPER_MODEL=base
ENV REDIS_URL=redis://redis:6379

CMD ["python", "main.py"]
