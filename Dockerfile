# jev-seo web app
#   docker compose up -d --build            (see CAI-DAT.md)
#   docker build -t jev-seo . && docker run -p 8000:8000 --env-file .env jev-seo
FROM python:3.12-slim

# WeasyPrint (PDF reports) needs Pango and HarfBuzz; fonts are bundled in jevseo/fonts.
RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN useradd --create-home --uid 10001 jevseo && mkdir -p /data && chown jevseo /data
USER jevseo

ENV PYTHONUNBUFFERED=1 PORT=8000 DATA_DIR=/data MPLCONFIGDIR=/tmp/matplotlib
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz', timeout=4)" || exit 1
CMD ["sh", "-c", "exec python -m jevseo serve --host 0.0.0.0 --port \"$PORT\" --data-dir \"$DATA_DIR\""]
