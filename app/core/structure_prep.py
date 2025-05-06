import os
from Bio import PDB
from Bio.PDB import *
from Bio.PDB.DSSP import dssp_dict_from_pdb_file
import numpy as np
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Descriptors3D
from pathlib import Path
import tempfile

class StructurePreparation:
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    def prepare_structure(self, pdb_file_path: str, workflow_id: str) -> dict:
        """
        Prepare protein structure for analysis:
        1. Load and validate PDB structure
        2. Add missing hydrogens
        3. Optimize hydrogen bonds
        4. Calculate molecular descriptors
        5. Save processed structure
        """
        try:
            import time # <-- Add this import at the top of the try block or beginning of file

            # Verify file exists, with retry for volume mount delay
            max_retries = 5
            retry_delay = 0.5 # seconds
            file_found = False
            for attempt in range(max_retries):
                if os.path.exists(pdb_file_path):
                    file_found = True
                    print(f"Found PDB file on attempt {attempt + 1}")
                    break
                else:
                    print(f"PDB file not found on attempt {attempt + 1}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)

            if not file_found:
                print(f"PDB file still not found after {max_retries} attempts.")
                return {
                    "status": "error",
                    "message": f"PDB file not found at path after retries: {pdb_file_path}"
                }

            # Create workflow directory
            workflow_dir = Path(self.upload_dir) / workflow_id
            workflow_dir.mkdir(exist_ok=True)
            print(f"Processing structure from {pdb_file_path} for workflow {workflow_id}")
            
            # Load structure using BioPython
            parser = PDB.PDBParser(QUIET=True)
            structure = parser.get_structure('protein', pdb_file_path)
            if not structure:
                raise ValueError("Failed to parse PDB file")

            # Get first model
            model = structure[0]
            
            # Basic structure validation
            if sum(1 for _ in model.get_residues()) == 0:
                raise ValueError("No residues found in structure")

            # Basic structure analysis
            num_residues = sum(1 for _ in model.get_residues())
            num_chains = len(model)
            num_atoms = sum(1 for _ in model.get_atoms())
            
            # Convert to RDKit molecule more efficiently
            with tempfile.NamedTemporaryFile(suffix='.pdb', mode='w') as tmp:
                io = PDBIO()
                io.set_structure(structure)
                io.save(tmp.name)
                mol = Chem.MolFromPDBFile(tmp.name, removeHs=False)
                if mol is None:
                    raise ValueError("Failed to convert structure to RDKit molecule")
                
                # Add hydrogens without optimization
                mol = Chem.AddHs(mol, addCoords=True)
                
                # Calculate molecular descriptors
                descriptors = {
                    # Basic protein properties
                    'num_residues': num_residues,
                    'num_chains': num_chains,
                    'num_atoms': num_atoms,
                    'molecular_weight': Descriptors.ExactMolWt(mol),
                    
                    # Structural properties
                    'num_bonds': mol.GetNumBonds(),
                    'num_rings': len(Chem.GetSSSR(mol)),
                    'formal_charge': Chem.GetFormalCharge(mol),
                    
                    # Drug-like properties
                    'num_rotatable_bonds': Descriptors.NumRotatableBonds(mol),
                    'num_h_acceptors': Descriptors.NumHAcceptors(mol),
                    'num_h_donors': Descriptors.NumHDonors(mol),
                    'tpsa': Descriptors.TPSA(mol),
                    'logp': Descriptors.MolLogP(mol)
                }
                
                # Save processed structure
                output_path = workflow_dir / 'processed.pdb'
                io.save(str(output_path))
                
                # Save descriptors to a JSON file
                import json
                results_file = workflow_dir / 'results.json'
                with open(results_file, 'w') as f:
                    json.dump({
                        "STRUCTURE_PREPARATION": {
                            "status": "success",
                            "descriptors": descriptors
                        }
                    }, f, indent=2)

            return {
                "status": "success",
                "message": "Structure processed successfully",
                "descriptors": descriptors
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_structure_info(self, workflow_id: str) -> dict:
        """Get information about a prepared structure"""
        try:
            workflow_dir = Path(self.upload_dir) / workflow_id
            
            if not workflow_dir.exists():
                raise ValueError(f"No prepared structure found for workflow {workflow_id}")

            structure_path = workflow_dir / 'prepared_structure.pdb'
            descriptors_path = workflow_dir / 'descriptors.npy'

            if not structure_path.exists() or not descriptors_path.exists():
                raise ValueError("Structure preparation incomplete")

            descriptors = np.load(descriptors_path, allow_pickle=True).item()

            return {
                'status': 'success',
                'descriptors': descriptors,
                'structure_path': str(structure_path)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
