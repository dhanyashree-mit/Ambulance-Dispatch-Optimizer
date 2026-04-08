FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 7860

# Start application using python -m to ensure package visibility
CMD ["python", "-m", "uvicorn", "environment:app", "--host", "0.0.0.0", "--port", "7860"]
