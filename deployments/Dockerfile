# Step 1: Build stage
FROM python:3.11-slim as builder

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

# Copy the rest of the app's source code
COPY . .

# Expose the port that the FastAPI app will run on
EXPOSE 80

# Command to run the FastAPI app
CMD ["fastapi", "run", "app/app.py", "--host", "0.0.0.0", "--port", "80"]
