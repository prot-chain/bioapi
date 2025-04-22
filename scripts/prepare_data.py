#!/usr/bin/env python3

import os
import json
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from Bio import SeqIO
from Bio.PDB import *
import torch
from transformers import AutoTokenizer, AutoModel

class DataPreparator:
    def __init__(self):
        self.protein_tokenizer = AutoTokenizer.from_pretrained('facebook/esm2_t33_650M_UR50D')
        self.protein_model = AutoModel.from_pretrained('facebook/esm2_t33_650M_UR50D')
        
    def process_protein_sequence(self, sequence):
        """Process protein sequence using ESM-2 embeddings"""
        # Tokenize sequence
        tokens = self.protein_tokenizer(sequence, return_tensors="pt", padding=True)
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.protein_model(**tokens)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return embeddings.numpy()
    
    def process_compound(self, mol):
        """Process compound using RDKit features"""
        if mol is None:
            return None
            
        # Calculate 2D fingerprints
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        
        # Calculate basic molecular properties
        props = {
            'MW': Chem.Descriptors.ExactMolWt(mol),
            'LogP': Chem.Descriptors.MolLogP(mol),
            'TPSA': Chem.Descriptors.TPSA(mol),
            'HBA': Chem.rdMolDescriptors.CalcNumHBA(mol),
            'HBD': Chem.rdMolDescriptors.CalcNumHBD(mol),
            'RotBonds': Chem.rdMolDescriptors.CalcNumRotatableBonds(mol)
        }
        
        return {
            'fingerprint': list(fp.ToBitString()),
            'properties': props
        }

def main(protein_sequence, compound_library, output_dir):
    # Initialize data preparator
    preparator = DataPreparator()
    
    # Process protein sequence
    protein_features = preparator.process_protein_sequence(protein_sequence)
    
    # Process compounds
    compounds = []
    suppl = Chem.SDMolSupplier(compound_library)
    for idx, mol in enumerate(suppl):
        if mol is not None:
            compound_data = preparator.process_compound(mol)
            if compound_data:
                compound_data['id'] = f"compound_{idx}"
                compound_data['smiles'] = Chem.MolToSmiles(mol)
                compounds.append(compound_data)
    
    # Save processed data
    output_data = {
        'protein_features': protein_features.tolist(),
        'compounds': compounds
    }
    
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'processed_data.json')
    with open(output_file, 'w') as f:
        json.dump(output_data, f)
    
    return output_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--protein_sequence', required=True)
    parser.add_argument('--compound_library', required=True)
    parser.add_argument('--output_dir', required=True)
    
    args = parser.parse_args()
    main(args.protein_sequence, args.compound_library, args.output_dir) 