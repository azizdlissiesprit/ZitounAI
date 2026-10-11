FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    MODEL_DIR=/models/m6 \
    TORCH_THREADS=4 \
    YOLO_OFFLINE=1 \
    YOLO_CONFIG_DIR=/tmp

WORKDIR /app
COPY requirements.txt .
# requirements.txt points pip to the CPU-only torch wheels.
# ultralytics depends on opencv-python (GUI build, needs libGL): swap it for the headless build.
RUN pip install -r requirements.txt \
    && pip uninstall -y opencv-python \
    && pip install --no-deps --force-reinstall opencv-python-headless==5.0.0.93

COPY app ./app

EXPOSE 8000
# The weights (5.5 MB) are mounted at /models, not baked into the image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/health')"
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
