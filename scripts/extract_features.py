#!/usr/bin/env python3

import os
import json
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors3D
import torch
from torch_geometric.data import Data
import torch_geometric.transforms as T

class FeatureExtractor:
    def __init__(self):
        self.atom_features = {
            'atomic_num': list(range(1, 119)),
            'degree': [0, 1, 2, 3, 4, 5, 6],
            'formal_charge': [-3, -2, -1, 0, 1, 2, 3],
            'hybridization': [
                Chem.rdchem.HybridizationType.SP,
                Chem.rdchem.HybridizationType.SP2,
                Chem.rdchem.HybridizationType.SP3,
                Chem.rdchem.HybridizationType.SP3D,
                Chem.rdchem.HybridizationType.SP3D2
            ],
            'is_aromatic': [0, 1]
        }
        
    def get_atom_features(self, atom):
        """Convert atom to feature vector"""
        features = []
        
        # Atomic number one-hot
        atomic_num = [0] * 118
        atomic_num[atom.GetAtomicNum()-1] = 1
        features.extend(atomic_num)
        
        # Degree one-hot
        degree = [0] * 7
        degree[min(atom.GetDegree(), 6)] = 1
        features.extend(degree)
        
        # Formal charge one-hot
        formal_charge = [0] * 7
        charge_idx = min(max(atom.GetFormalCharge()+3, 0), 6)
        formal_charge[charge_idx] = 1
        features.extend(formal_charge)
        
        # Hybridization one-hot
        hybridization = [0] * 5
        hyb_type = str(atom.GetHybridization())
        if hyb_type == 'SP':
            hybridization[0] = 1
        elif hyb_type == 'SP2':
            hybridization[1] = 1
        elif hyb_type == 'SP3':
            hybridization[2] = 1
        elif hyb_type == 'SP3D':
            hybridization[3] = 1
        elif hyb_type == 'SP3D2':
            hybridization[4] = 1
        features.extend(hybridization)
        
        # Is aromatic
        features.append(int(atom.GetIsAromatic()))
        
        return np.array(features)
    
    def mol_to_graph_data(self, mol):
        """Convert molecule to graph data format"""
        # Get atom features
        num_atoms = mol.GetNumAtoms()
        atom_features = []
        for atom_idx in range(num_atoms):
            atom = mol.GetAtomWithIdx(atom_idx)
            atom_features.append(self.get_atom_features(atom))
        x = torch.tensor(np.array(atom_features), dtype=torch.float)
        
        # Get edge indices and features
        edges = []
        edge_features = []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            
            # Add edges in both directions
            edges.append([i, j])
            edges.append([j, i])
            
            # Bond type one-hot
            bond_type = bond.GetBondType()
            if bond_type == Chem.rdchem.BondType.SINGLE:
                edge_feature = [1, 0, 0, 0]
            elif bond_type == Chem.rdchem.BondType.DOUBLE:
                edge_feature = [0, 1, 0, 0]
            elif bond_type == Chem.rdchem.BondType.TRIPLE:
                edge_feature = [0, 0, 1, 0]
            elif bond_type == Chem.rdchem.BondType.AROMATIC:
                edge_feature = [0, 0, 0, 1]
            else:
                edge_feature = [0, 0, 0, 0]
            
            edge_features.extend([edge_feature, edge_feature])
        
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(np.array(edge_features), dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

def main(input_file, output_dir):
    # Load processed data
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Initialize feature extractor
    extractor = FeatureExtractor()
    
    # Process each compound
    processed_compounds = []
    for compound in data['compounds']:
        # Convert SMILES to molecule
        mol = Chem.MolFromSmiles(compound['smiles'])
        if mol is None:
            continue
            
        # Generate 3D conformation
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        AllChem.MMFFOptimizeMolecule(mol)
        
        # Extract graph features
        graph_data = extractor.mol_to_graph_data(mol)
        
        # Calculate 3D descriptors
        descriptors_3d = {
            'PMI1': Descriptors3D.PMI1(mol),
            'PMI2': Descriptors3D.PMI2(mol),
            'PMI3': Descriptors3D.PMI3(mol),
            'SpherocityIndex': Descriptors3D.SpherocityIndex(mol),
            'NPR1': Descriptors3D.NPR1(mol),
            'NPR2': Descriptors3D.NPR2(mol)
        }
        
        # Combine all features
        compound_features = {
            'id': compound['id'],
            'graph_data': {
                'x': graph_data.x.tolist(),
                'edge_index': graph_data.edge_index.tolist(),
                'edge_attr': graph_data.edge_attr.tolist()
            },
            'molecular_descriptors': {
                **compound['properties'],
                **descriptors_3d
            }
        }
        processed_compounds.append(compound_features)
    
    # Combine with protein features
    output_data = {
        'protein_features': data['protein_features'],
        'compounds': processed_compounds
    }
    
    # Save features
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'feature_vectors.json')
    with open(output_file, 'w') as f:
        json.dump(output_data, f)
    
    return output_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', required=True)
    parser.add_argument('--output_dir', required=True)
    
    args = parser.parse_args()
    main(args.input_file, args.output_dir) 