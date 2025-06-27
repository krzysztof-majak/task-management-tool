FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && python -m compileall .

COPY . .

RUN mkdir -p /app/data \
 && addgroup --system appuser \
 && adduser  --system --ingroup appuser --home /app appuser \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
