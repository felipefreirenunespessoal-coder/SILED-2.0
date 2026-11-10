FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SILED_DATA_DIR=/var/data HOST=0.0.0.0 PORT=5000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home siled && mkdir -p /var/data && chown siled:siled /var/data
COPY --chown=siled:siled . .
USER siled
EXPOSE 5000
CMD ["python", "main.py"]
