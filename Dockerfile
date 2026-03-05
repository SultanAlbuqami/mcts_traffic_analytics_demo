FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TRAFFIC_ANALYTICS_LLM_PROVIDER=disabled \
    TRAFFIC_ANALYTICS_LOG_LEVEL=INFO

WORKDIR /app

# Install curl for healthcheck before dropping privileges
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid 1001 --no-create-home --shell /bin/false appuser

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY docs ./docs
COPY data ./data

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip install -e . \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fs http://127.0.0.1:8501/_stcore/health || exit 1

CMD ["sh", "-c", "python -m traffic_analytics_demo.cli all && streamlit run app/streamlit_app.py --server.address=0.0.0.0 --server.port=${TRAFFIC_ANALYTICS_STREAMLIT_PORT:-8501}"]
