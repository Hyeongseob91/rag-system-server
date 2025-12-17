FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./

RUN uv pip install --system -e .

COPY . .

RUN mkdir -p /app/uploads

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8188

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8188"]
