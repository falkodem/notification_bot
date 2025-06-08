FROM python:3.12-alpine

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN adduser -D botuser && \
    chown -R botuser:botuser /app
USER botuser

CMD ["python", "main.py"]