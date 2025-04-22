# ProtChain BioAPI

A blockchain-powered platform for protein analysis and AI-driven drug discovery, enabling researchers to predict and validate protein-drug interactions across various therapeutic targets.

## Features

- **Protein Analysis**: 
  - Process and analyze protein sequences using state-of-the-art language models
  - Support for 3D structure analysis with PDB files
  - Binding site identification and analysis
  
- **Drug Discovery**: 
  - Virtual screening of compound libraries
  - AI-driven prediction of protein-drug interactions
  - Multi-property optimization (binding affinity, selectivity, etc.)
  
- **AI/ML Models**: 
  - Graph Neural Networks for molecular property prediction
  - Transformer models for protein-compound interaction prediction
  - Multiple model types supported (transformer, CNN, graph-neural-network)
  
- **Blockchain Integration**: 
  - Immutable record of predictions and results
  - IPFS storage for detailed data
  - Verifiable research outcomes
  
- **Comprehensive Reporting**:
  - Interactive visualizations
  - Molecular property analysis
  - Validation against drug-likeness criteria
  - Blockchain verification

## Workflows

### Protein-Drug Interaction Prediction

This workflow predicts potential drug candidates for any protein target using AI/ML models:

1. **Data Preparation**
   - Process protein sequences using ESM-2 embeddings
   - Optional 3D structure analysis with PDB files
   - Convert compounds to molecular graphs
   - Calculate molecular descriptors

2. **Feature Extraction**
   - Generate molecular fingerprints
   - Extract structural features
   - Calculate 3D molecular properties
   - Analyze binding site characteristics

3. **Model Prediction**
   - Score compounds against target protein
   - Optimize for specific properties (binding affinity, selectivity, etc.)
   - Apply confidence thresholds
   - Rank potential drug candidates

4. **Result Validation**
   - Validate against Lipinski's Rule of Five
   - Check molecular properties
   - Store results on blockchain

5. **Report Generation**
   - Generate interactive visualizations
   - Create detailed analysis reports
   - Provide blockchain verification

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the blockchain network:
   ```bash
   cd ../protchain/deployments
   ./setup.sh
   ```

3. Start the API server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

1. Submit a workflow:
   ```bash
   curl -X POST "http://localhost:8000/workflows" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "protein_drug_prediction",
          "template": "protein-drug-interaction",
          "parameters": {
            "protein_sequence": "YOUR_PROTEIN_SEQUENCE",
            "protein_name": "YOUR_PROTEIN_NAME",
            "protein_pdb": "path/to/structure.pdb",
            "compound_library": "path/to/compounds.sdf",
            "model_type": "graph-neural-network",
            "confidence_threshold": 0.8,
            "binding_site": "A123,B456,C789",
            "target_property": "binding_affinity"
          }
        }'
   ```

2. Monitor workflow status:
   ```bash
   curl "http://localhost:8000/workflows/{workflow_id}"
   ```

3. Get results:
   ```bash
   curl "http://localhost:8000/workflows/{workflow_id}/results"
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
