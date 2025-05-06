from fastapi import APIRouter, HTTPException, UploadFile, File
from Bio.PDB import *
from Bio.PDB.DSSP import dssp_dict_from_pdb_file
import requests
import numpy as np
from typing import List, Dict, Optional
import os
import json
import prody as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms
import tempfile
import ipfshttpclient

router = APIRouter()
PDB_BASE_URL = "https://files.rcsb.org/download/"
CACHE_DIR = "/app/data/pdb_cache"

class PDBHandler:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.parser = PDBParser(QUIET=True)
        # Connect to IPFS using the Docker service name
        self.ipfs = ipfshttpclient.connect('/dns/ipfs-kubo/tcp/5001')
        
    def _calculate_binding_sites(self, structure) -> List[Dict]:
        """Calculate potential binding sites using cavity detection"""
        binding_sites = []
        
        # Convert structure to ProDy molecule
        pdb = pd.parsePDB(structure.get_id())
        
        # Calculate protein surface
        surface = pd.calcMSMS(pdb, probe_radius=1.4)
        
        # Identify cavities (simplified algorithm)
        cavities = pd.findDepressions(surface, min_depth=4.0)
        
        for i, cavity in enumerate(cavities):
            center = cavity.getCenter()
            volume = cavity.getVolume()
            residues = cavity.getResidues()
            
            binding_sites.append({
                'id': f'site_{i+1}',
                'center': center.tolist(),
                'volume': float(volume),
                'residues': [str(res) for res in residues],
                'score': self._score_binding_site(cavity)
            })
            
        return binding_sites
        
    def _score_binding_site(self, cavity) -> float:
        """Score binding site based on various properties"""
        # Implement a scoring function based on:
        # - Cavity volume
        # - Hydrophobicity
        # - Conservation scores
        # - Electrostatic potential
        # This is a simplified version
        volume_score = min(cavity.getVolume() / 1000, 1.0)
        hydrophobicity = self._calculate_hydrophobicity(cavity)
        
        return (volume_score + hydrophobicity) / 2
        
    def _calculate_hydrophobicity(self, cavity) -> float:
        """Calculate hydrophobicity of cavity residues"""
        # Kyte-Doolittle hydrophobicity scale
        hydrophobicity_scale = {
            'ILE': 4.5, 'VAL': 4.2, 'LEU': 3.8, 'PHE': 2.8,
            'CYS': 2.5, 'MET': 1.9, 'ALA': 1.8, 'GLY': -0.4,
            'THR': -0.7, 'SER': -0.8, 'TRP': -0.9, 'TYR': -1.3,
            'PRO': -1.6, 'HIS': -3.2, 'GLU': -3.5, 'GLN': -3.5,
            'ASP': -3.5, 'ASN': -3.5, 'LYS': -3.9, 'ARG': -4.5
        }
        
        total = 0
        count = 0
        for residue in cavity.getResidues():
            if residue.getResname() in hydrophobicity_scale:
                total += hydrophobicity_scale[residue.getResname()]
                count += 1
                
        return (total / count) if count > 0 else 0
        
    async def download_pdb(self, pdb_id: str) -> str:
        """Download PDB file and return its path"""
        cache_path = os.path.join(CACHE_DIR, f"{pdb_id}.pdb")
        if os.path.exists(cache_path):
            return cache_path
            
        url = f"{PDB_BASE_URL}{pdb_id}.pdb"
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"PDB {pdb_id} not found")
            
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        return cache_path
        
    async def analyze_structure(self, pdb_path: str) -> Dict:
        """Analyze PDB structure and return comprehensive metadata"""
        structure = self.parser.get_structure('protein', pdb_path)
        
        # Basic structure information
        metadata = {
            'basic_info': {
                'chains': len(list(structure.get_chains())),
                'residues': sum(1 for _ in structure.get_residues()),
                'atoms': sum(1 for _ in structure.get_atoms()),
                'models': len(structure)
            }
        }
        
        # Calculate secondary structure
        with tempfile.NamedTemporaryFile(suffix='.pdb') as tmp:
            io = PDBIO()
            io.set_structure(structure)
            io.save(tmp.name)
            dssp_dict = dssp_dict_from_pdb_file(tmp.name)[0]
            
        sec_struct_stats = {'helix': 0, 'sheet': 0, 'loop': 0}
        for _, props in dssp_dict.items():
            ss = props[2]
            if ss in ['H', 'G', 'I']:  # Helices
                sec_struct_stats['helix'] += 1
            elif ss in ['B', 'E']:  # Sheets
                sec_struct_stats['sheet'] += 1
            else:  # Loops and others
                sec_struct_stats['loop'] += 1
                
        metadata['secondary_structure'] = sec_struct_stats
        
        # Calculate binding sites
        metadata['binding_sites'] = self._calculate_binding_sites(structure)
        
        # Calculate structural properties
        metadata['structural_properties'] = {
            'radius_of_gyration': self._calculate_radius_of_gyration(structure),
            'surface_area': self._calculate_surface_area(structure),
            'charge_distribution': self._calculate_charge_distribution(structure)
        }
        
        return metadata
        
    def _calculate_radius_of_gyration(self, structure) -> float:
        """Calculate radius of gyration"""
        coords = []
        masses = []
        
        for atom in structure.get_atoms():
            coords.append(atom.get_coord())
            masses.append(atom.mass)
            
        coords = np.array(coords)
        masses = np.array(masses)
        center = np.average(coords, weights=masses, axis=0)
        
        rg = np.sqrt(np.sum(masses * np.sum((coords - center)**2, axis=1)) / np.sum(masses))
        return float(rg)
        
    def _calculate_surface_area(self, structure) -> float:
        """Calculate molecular surface area"""
        # Using ProDy for surface area calculation
        pdb = pd.parsePDB(structure.get_id())
        surface = pd.calcMSMS(pdb, probe_radius=1.4)
        return float(surface.getArea())
        
    def _calculate_charge_distribution(self, structure) -> Dict:
        """Calculate charge distribution"""
        charges = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for residue in structure.get_residues():
            if residue.resname in ['ARG', 'LYS', 'HIS']:
                charges['positive'] += 1
            elif residue.resname in ['ASP', 'GLU']:
                charges['negative'] += 1
            else:
                charges['neutral'] += 1
                
        return charges

pdb_handler = PDBHandler()

@router.get("/pdb/{pdb_id}")
async def get_pdb_file(pdb_id: str):
    """Download and return PDB file"""
    try:
        file_path = await pdb_handler.download_pdb(pdb_id)
        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdb/{pdb_id}/metadata")
async def get_pdb_metadata(pdb_id: str):
    """Get PDB file metadata"""
    try:
        file_path = await pdb_handler.download_pdb(pdb_id)
        metadata = pdb_handler.analyze_structure(file_path)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
