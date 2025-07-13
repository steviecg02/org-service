FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt dev-requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -r dev-requirements.txt

# Copy project
COPY . .

# Expose port and run
EXPOSE 8000
CMD ["uvicorn", "org_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
