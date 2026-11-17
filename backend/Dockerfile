FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OCP/VTK wheels need these shared libraries, even for headless CAD imports.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglu1-mesa libxrender1 libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-runtime.txt ./
RUN pip install -r requirements-runtime.txt

COPY . .
RUN python -c "from build123d import Box; from geometry.measurements.bbox import compute_bbox_occ; assert compute_bbox_occ(Box(1, 2, 3).wrapped).width > 0"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
