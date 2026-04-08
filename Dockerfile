FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Install dependencies using the lock file
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache .

# Copy project modules
COPY tasks/ tasks/
COPY graders/ graders/
COPY data/ data/
COPY server/ server/
COPY openenv.yaml .
COPY README.md .

# Expose port
EXPOSE 7860

# Start application using the new server entry point
CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
