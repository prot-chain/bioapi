#!/usr/bin/env python3

import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
from transformers import AutoModel

class ProteinCompoundInteractionModel(nn.Module):
    def __init__(self, protein_dim=1280, num_graph_features=131):
        super().__init__()
        
        # Protein feature processing
        self.protein_fc = nn.Sequential(
            nn.Linear(protein_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256)
        )
        
        # Graph neural network for compounds
        self.conv1 = GCNConv(num_graph_features, 128)
        self.conv2 = GCNConv(128, 128)
        self.conv3 = GCNConv(128, 128)
        
        # Molecular descriptor processing
        self.descriptor_fc = nn.Sequential(
            nn.Linear(12, 64),  # 6 2D + 6 3D descriptors
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Final prediction layers
        self.fc = nn.Sequential(
            nn.Linear(448, 256),  # 256 (protein) + 128 (graph) + 64 (descriptors)
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
    
    def forward(self, protein_features, graph_data, molecular_descriptors):
        # Process protein features
        protein_out = self.protein_fc(protein_features)
        
        # Process graph features
        x, edge_index, edge_attr = graph_data
        x = F.relu(self.conv1(x, edge_index, edge_attr))
        x = F.relu(self.conv2(x, edge_index, edge_attr))
        x = F.relu(self.conv3(x, edge_index, edge_attr))
        graph_out = global_mean_pool(x, torch.zeros(x.size(0), dtype=torch.long))
        
        # Process molecular descriptors
        desc_out = self.descriptor_fc(molecular_descriptors)
        
        # Combine all features
        combined = torch.cat([protein_out, graph_out, desc_out], dim=1)
        
        # Final prediction
        out = self.fc(combined)
        return torch.sigmoid(out)

def load_model(model_type):
    """Load the appropriate model based on type"""
    if model_type == 'graph-neural-network':
        model = ProteinCompoundInteractionModel()
        model.load_state_dict(torch.load('/app/models/gnn_model.pth'))
    elif model_type == 'transformer':
        model = AutoModel.from_pretrained('/app/models/transformer_model')
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    model.eval()
    return model

def prepare_batch(compound, protein_features):
    """Prepare a single compound batch for prediction"""
    # Process graph data
    x = torch.tensor(compound['graph_data']['x'], dtype=torch.float)
    edge_index = torch.tensor(compound['graph_data']['edge_index'], dtype=torch.long)
    edge_attr = torch.tensor(compound['graph_data']['edge_attr'], dtype=torch.float)
    
    # Process molecular descriptors
    descriptors = []
    desc_dict = compound['molecular_descriptors']
    for key in ['MW', 'LogP', 'TPSA', 'HBA', 'HBD', 'RotBonds',
                'PMI1', 'PMI2', 'PMI3', 'SpherocityIndex', 'NPR1', 'NPR2']:
        descriptors.append(desc_dict[key])
    molecular_descriptors = torch.tensor([descriptors], dtype=torch.float)
    
    # Process protein features
    protein_features = torch.tensor([protein_features], dtype=torch.float)
    
    return protein_features, (x, edge_index, edge_attr), molecular_descriptors

def main(input_file, model_type, confidence_threshold, output_dir):
    # Load data
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Load model
    model = load_model(model_type)
    
    # Make predictions
    predictions = []
    protein_features = data['protein_features']
    
    with torch.no_grad():
        for compound in data['compounds']:
            # Prepare batch
            batch = prepare_batch(compound, protein_features)
            
            # Get prediction
            score = model(*batch).item()
            
            if score >= confidence_threshold:
                prediction = {
                    'compound_id': compound['id'],
                    'score': score,
                    'molecular_properties': compound['molecular_descriptors']
                }
                predictions.append(prediction)
    
    # Sort predictions by score
    predictions.sort(key=lambda x: x['score'], reverse=True)
    
    # Save predictions
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'predictions.json')
    with open(output_file, 'w') as f:
        json.dump({
            'predictions': predictions,
            'model_type': model_type,
            'confidence_threshold': confidence_threshold
        }, f, indent=2)
    
    return output_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', required=True)
    parser.add_argument('--model_type', required=True)
    parser.add_argument('--confidence_threshold', type=float, required=True)
    parser.add_argument('--output_dir', required=True)
    
    args = parser.parse_args()
    main(args.input_file, args.model_type, args.confidence_threshold, args.output_dir) 