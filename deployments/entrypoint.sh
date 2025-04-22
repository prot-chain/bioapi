#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p /app/data/templates
mkdir -p /app/data/workflows
mkdir -p /app/data/workflow_results
mkdir -p /app/data/workflow_state
mkdir -p /app/bin

# Set default environment variables if not set
export FABRIC_CONFIG_PATH=${FABRIC_CONFIG_PATH:-"/config/connection-profile.json"}
export FABRIC_CHANNEL=${FABRIC_CHANNEL:-"mychannel"}
export FABRIC_CHAINCODE=${FABRIC_CHAINCODE:-"proteomic"}
export FABRIC_ORG=${FABRIC_ORG:-"org1.example.com"}
export FABRIC_USER=${FABRIC_USER:-"Admin"}
export WORKFLOW_BINARY_PATH=${WORKFLOW_BINARY_PATH:-"/app/bin/protchainworkflow"}
export DATA_DIR=${DATA_DIR:-"/app/data"}
export BIOAPI_ENV=${BIOAPI_ENV:-"local"}
export CRYPTO_PATH=${CRYPTO_PATH:-"/crypto/org1"}
export MSPID=${MSPID:-"Org1MSP"}
export PEER_ENDPOINT=${PEER_ENDPOINT:-"peer0.org1.example.com:7051"}

# Execute the command passed to the container
exec "$@" 