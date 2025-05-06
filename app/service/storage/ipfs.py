"""IPFS storage service for PDB files."""

import hashlib
import requests
import json

def calculate_hash(content: str) -> str:
    """Calculate SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()

async def store_on_ipfs(content: str) -> str:
    """Store content on IPFS and return the CID."""
    try:
        # Use the HTTP API directly instead of the client library
        # This works with any IPFS version
        # Use the Docker service name for communication between containers
        url = 'http://ipfs:5001/api/v0/add' # Match the service name in docker-compose.yml
        files = {
            'file': ('pdb_file.pdb', content)
        }
        
        response = requests.post(url, files=files)
        
        if response.status_code != 200:
            raise Exception(f"IPFS API error: {response.text}")
            
        result = json.loads(response.text)
        return result['Hash']
    except Exception as e:
        raise Exception(f"Failed to store file on IPFS: {str(e)}")
