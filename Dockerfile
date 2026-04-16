FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.111.0" \
    "uvicorn[standard]>=0.29.0" \
    "httpx>=0.27.0" \
    "pydantic>=2,<3" \
    "pydantic-settings>=2.2.0" \
    "pyyaml>=6.0"

ENV PYTHONUNBUFFERED=1

COPY main.py .
COPY src/ src/
COPY comment_templates.yaml .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
