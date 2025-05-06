# Step 1: Build stage
FROM python:3.11-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    swig \
    libopenbabel-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Open Babel build
ENV CPLUS_INCLUDE_PATH=/usr/include/openbabel3
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies into a separate directory
RUN pip install --no-cache-dir -r requirements.txt

# Step 2: Final stage
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy installed Python packages AND binaries from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Add Python's bin directory (where uvicorn is) to PATH
ENV PATH=/usr/local/bin:$PATH
# Set PYTHONPATH to fix import issues
ENV PYTHONPATH=/app

# Install additional dependencies
RUN apt-get update && apt-get install -y curl && \
    pip install pyyaml

# Create necessary directories
RUN mkdir -p /app/data/templates /app/data/workflows /app/data/workflow_results /app/data/workflow_state /app/bin

# Set default environment variables
ENV FABRIC_CONFIG_PATH=/config/connection-profile.json
ENV FABRIC_CHANNEL=mychannel
ENV FABRIC_CHAINCODE=proteomic
ENV FABRIC_ORG=org1.example.com
ENV FABRIC_USER=Admin
ENV WORKFLOW_BINARY_PATH=/app/bin/protchainworkflow
ENV DATA_DIR=/app/data
ENV BIOAPI_ENV=local
ENV CRYPTO_PATH=/crypto/org1
ENV MSPID=Org1MSP
ENV PEER_ENDPOINT=peer0.org1.example.com:7051

# Copy the rest of the app's source code
COPY . .

# Make sure the script is executable after copying
RUN chmod +x /app/entrypoint.sh

# Expose the port that the FastAPI app will run on
EXPOSE 80

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
# Command to run the FastAPI app
CMD ["fastapi", "run", "app/app.py", "--host", "0.0.0.0", "--port", "80"]