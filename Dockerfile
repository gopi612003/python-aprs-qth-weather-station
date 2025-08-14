FROM python:3.11-slim

LABEL maintainer="N1k0droid\\IT9KVB" \
      description="Python APRS QTH Weather Station" \
      version="4.1"

WORKDIR /app

RUN pip install --no-cache-dir flask aprslib configparser

COPY app.py .
COPY aprs_send.py .
COPY aprs_send_daemon.py .
COPY start_services.py .

RUN mkdir -p /defaults /config

COPY aprs_config.ini /defaults/aprs_config.ini
RUN cp /defaults/aprs_config.ini /config/aprs_config.ini

VOLUME ["/config"]

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["python3", "/app/start_services.py"]
