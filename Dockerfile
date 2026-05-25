FROM python:3.11-slim
WORKDIR /app

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python","run.py","--playlist-store","config/playlists.json"]
