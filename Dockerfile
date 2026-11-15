FROM python:3.12-slim
WORKDIR /workspace
RUN pip install --no-cache-dir uv==0.13.8
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --extra warehouse --no-dev
COPY . .
ENV PATH="/workspace/.venv/bin:$PATH" PYTHONUNBUFFERED=1
CMD ["uvicorn", "commerce.api:app", "--host", "0.0.0.0", "--port", "8000"]
