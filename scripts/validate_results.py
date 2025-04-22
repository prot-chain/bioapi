#!/usr/bin/env python3

import os
import json
import hashlib
import requests
from datetime import datetime

class BlockchainClient:
    def __init__(self):
        self.api_url = "http://localhost:3000/api/blockchain"
        self.ipfs_url = "http://localhost:5001/api/v0"
    
    def store_on_ipfs(self, data):
        """Store data on IPFS"""
        files = {
            'file': ('data.json', json.dumps(data))
        }
        response = requests.post(f"{self.ipfs_url}/add", files=files)
        if response.status_code == 200:
            return response.json()['Hash']
        else:
            raise Exception("Failed to store data on IPFS")
    
    def store_on_blockchain(self, data_hash, metadata):
        """Store hash and metadata on blockchain"""
        payload = {
            'hash': data_hash,
            'metadata': metadata
        }
        response = requests.post(f"{self.api_url}/store", json=payload)
        if response.status_code != 200:
            raise Exception("Failed to store data on blockchain")
        return response.json()

def validate_predictions(predictions, confidence_threshold):
    """Validate prediction results"""
    validation_results = {
        'total_compounds': len(predictions),
        'compounds_above_threshold': 0,
        'average_score': 0,
        'validation_checks': []
    }
    
    total_score = 0
    for pred in predictions:
        # Check confidence score
        if pred['score'] >= confidence_threshold:
            validation_results['compounds_above_threshold'] += 1
        
        total_score += pred['score']
        
        # Validate molecular properties
        props = pred['molecular_properties']
        checks = []
        
        # Lipinski's Rule of Five checks
        if props['MW'] <= 500:
            checks.append(('MW_CHECK', True, 'Molecular weight within limits'))
        else:
            checks.append(('MW_CHECK', False, 'Molecular weight exceeds 500'))
            
        if props['LogP'] <= 5:
            checks.append(('LOGP_CHECK', True, 'LogP within limits'))
        else:
            checks.append(('LOGP_CHECK', False, 'LogP exceeds 5'))
            
        if props['HBA'] <= 10:
            checks.append(('HBA_CHECK', True, 'Hydrogen bond acceptors within limits'))
        else:
            checks.append(('HBA_CHECK', False, 'Too many hydrogen bond acceptors'))
            
        if props['HBD'] <= 5:
            checks.append(('HBD_CHECK', True, 'Hydrogen bond donors within limits'))
        else:
            checks.append(('HBD_CHECK', False, 'Too many hydrogen bond donors'))
        
        validation_results['validation_checks'].append({
            'compound_id': pred['compound_id'],
            'checks': checks
        })
    
    validation_results['average_score'] = total_score / len(predictions) if predictions else 0
    return validation_results

def main(input_file, output_dir):
    # Load predictions
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    predictions = data['predictions']
    confidence_threshold = data['confidence_threshold']
    
    # Validate predictions
    validation_results = validate_predictions(predictions, confidence_threshold)
    
    # Prepare metadata for blockchain
    metadata = {
        'timestamp': datetime.utcnow().isoformat(),
        'model_type': data['model_type'],
        'confidence_threshold': confidence_threshold,
        'total_compounds': validation_results['total_compounds'],
        'compounds_above_threshold': validation_results['compounds_above_threshold'],
        'average_score': validation_results['average_score']
    }
    
    # Calculate hash of predictions
    predictions_hash = hashlib.sha256(
        json.dumps(predictions, sort_keys=True).encode()
    ).hexdigest()
    
    # Store results
    blockchain_client = BlockchainClient()
    
    # Store full results on IPFS
    full_results = {
        'predictions': predictions,
        'validation_results': validation_results,
        'metadata': metadata
    }
    ipfs_hash = blockchain_client.store_on_ipfs(full_results)
    
    # Store reference on blockchain
    blockchain_data = {
        'predictions_hash': predictions_hash,
        'ipfs_hash': ipfs_hash,
        **metadata
    }
    blockchain_receipt = blockchain_client.store_on_blockchain(
        predictions_hash,
        blockchain_data
    )
    
    # Save validated results
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'validated_results.json')
    with open(output_file, 'w') as f:
        json.dump({
            'predictions': predictions,
            'validation_results': validation_results,
            'blockchain_data': blockchain_data,
            'blockchain_receipt': blockchain_receipt
        }, f, indent=2)
    
    return output_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', required=True)
    parser.add_argument('--output_dir', required=True)
    
    args = parser.parse_args()
    main(args.input_file, args.output_dir) 