FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/

USER appuser
EXPOSE 8081

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
	CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/health')"

CMD ["python", "-m", "app.app"]
