# jev-seo web app: docker build -t jev-seo . && docker run -p 8000:8000 --env-file .env jev-seo
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1 PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m jevseo serve --host 0.0.0.0 --port ${PORT} --data-dir /tmp/jev-seo-web"]
