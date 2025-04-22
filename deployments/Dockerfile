# Step 1: Build stage
FROM python:3.11-slim AS builder

# Set the working directory inside the container
WORKDIR /app

# Install build dependencies (e.g., gcc for compiling Python packages)
RUN apt-get update && apt-get install -y build-essential

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies into a separate directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Step 2: Final stage
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the necessary files from the build stage (without dependencies)
COPY --from=builder /root/.local /root/.local

# Add Python to PATH environment variable
ENV PATH=/root/.local/bin:$PATH
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

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the app's source code
COPY . .

# Expose the port that the FastAPI app will run on
EXPOSE 80

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
# Command to run the FastAPI app
CMD ["fastapi", "run", "app/app.py", "--host", "0.0.0.0", "--port", "80"]