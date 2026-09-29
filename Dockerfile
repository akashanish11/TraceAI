FROM python:3.12-slim

WORKDIR /app

# Docker Desktop proxy
ENV HTTP_PROXY=http://http.docker.internal:3128
ENV HTTPS_PROXY=http://http.docker.internal:3128
ENV NO_PROXY=localhost,127.0.0.1

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.14.0

# Install remaining backend dependencies
COPY requirements-docker.txt .

RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]