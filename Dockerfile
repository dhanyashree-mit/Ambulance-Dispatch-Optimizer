FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project configuration AND all source code first
# This ensures setuptools can find packages (tasks, server, etc.) and README.md during installation
COPY pyproject.toml uv.lock README.md openenv.yaml ./
COPY tasks/ tasks/
COPY graders/ graders/
COPY data/ data/
COPY server/ server/

# Install the project and dependencies using the lock file
RUN uv pip install --system --no-cache .

# Expose port
EXPOSE 7860

# Start application using the new server entry point
CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
