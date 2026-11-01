# RoadAnomaly inference image: FastAPI (port 8000) and the Streamlit demo (port 8501).
# Build from the repository root:  docker compose -f deployment/docker-compose.yml build
# CPU TensorFlow keeps the image portable; the trained models are mounted from ./models at run time.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    ROADANOMALY_ROOT=/app \
    MPLBACKEND=Agg \
    KERAS_HOME=/opt/keras

WORKDIR /app

# Same pins as the notebooks (single source: requirements.txt), with tensorflow-cpu instead of
# tensorflow[and-cuda], and without the Jupyter tooling
COPY requirements.txt /tmp/requirements.txt
COPY deployment/requirements.txt /tmp/deployment-requirements.txt
RUN grep -E '^(keras|numpy|pandas|scipy|scikit-learn|matplotlib|pillow)==.*python_version >= "3.11"' \
        /tmp/requirements.txt > /tmp/runtime.txt \
    && pip install tensorflow-cpu==2.20.0 -r /tmp/runtime.txt -r /tmp/deployment-requirements.txt

# Shared code, then bake the frozen ImageNet backbone used by the feature autoencoder (about 58 MB)
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-deps -e . \
    && python -c "import keras; keras.applications.VGG16(include_top=False, weights='imagenet')"

COPY deployment ./deployment
COPY splits ./splits
COPY data/raw ./data/raw
COPY reports/results ./reports/results

# Unprivileged user; models/ is mounted read-only by docker-compose
RUN useradd --create-home --uid 1000 app && mkdir -p /app/models && chown -R app:app /app /opt/keras
USER app

EXPOSE 8000 8501
CMD ["uvicorn", "deployment.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
