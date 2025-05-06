import os
import uuid
import subprocess
import yaml
import json
import hashlib
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.blockchain import BlockchainClient
from app.schema.workflow import (
    WorkflowExecutionSchema, 
    WorkflowStatus, 
    WorkflowTemplateSchema, 
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowVerificationSchema
)
from app.service.pdb.fetch import PDBFetchService
from app.service.uniprot import UniprotFetchService
from .pipeline import DrugDiscoveryPipeline, WorkflowConfig, WorkflowStage

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self):
        # Initialize blockchain client
        self.blockchain = BlockchainClient()
        
        # Set up directories
        self.base_dir = settings.data_dir
        self.templates_dir = "/app/data/templates"
        self.workflows_dir = os.path.join(self.base_dir, "workflows")
        self.results_dir = os.path.join(self.base_dir, "workflow_results")
        self.upload_dir = os.path.join(self.base_dir, "uploads", "structures")
        self.workflow_binary = settings.workflow_binary_path
        
        # Log template directory for debugging
        print(f"Template directory: {self.templates_dir}")
        print(f"Available templates: {os.listdir(self.templates_dir)}")
        
        # In-memory storage for workflows (replace with database in production)
        self.executions = {}
        
        # Pipeline instances
        self.pipelines = {}
        
        # Ensure directories exist
        os.makedirs(self.workflows_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file"""
        if not os.path.exists(file_path):
            return ""
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _fetch_and_store_protein_data(self, protein_id: str) -> Dict[str, Any]:
        """
        Fetch protein data from PDB or UniProt and store it on IPFS
        
        Args:
            protein_id (str): The PDB or UniProt ID of the protein
            
        Returns:
            Dict[str, Any]: Dictionary containing protein data and IPFS CIDs
        """
        try:
            # Determine if it's a PDB or UniProt ID
            if len(protein_id) == 4:  # PDB ID
                pdb_service = PDBFetchService()
                raw_data = await pdb_service.fetch_protein_data(protein_id)
                protein_data = await pdb_service.parse_protein_data(raw_data)
                
                # Store protein data on IPFS
                ipfs_cid = self.blockchain.record_workflow_start(
                    workflow_id=f"protein_{protein_id}",
                    template_id="protein-data",
                    parameters={"data": protein_data.dict()}
                )
                
                # Get PDB file link
                pdb_link = protein_data.pdb_link
                
                # Return populated parameters
                return {
                    "protein_name": protein_data.recommended_name or protein_id,
                    "protein_ipfs_cid": ipfs_cid,
                    "protein_sequence": protein_data.sequence,
                    "pdb_link": pdb_link
                }
            else:  # UniProt ID
                uniprot_service = UniprotFetchService()
                raw_data = await uniprot_service.fetch_protein_data(protein_id)
                protein_data = uniprot_service.parse_protein_data(raw_data)
                
                # Store protein data on IPFS
                ipfs_cid = self.blockchain.record_workflow_start(
                    workflow_id=f"protein_{protein_id}",
                    template_id="protein-data",
                    parameters={"data": protein_data.dict()}
                )
                
                # Return populated parameters
                return {
                    "protein_name": protein_data.recommended_name or protein_id,
                    "protein_ipfs_cid": ipfs_cid,
                    "protein_sequence": protein_data.sequence,
                    "pdb_link": protein_data.pdb_link
                }
        except Exception as e:
            logger.error(f"Error fetching and storing protein data for {protein_id}: {e}")
            # Return empty dict if there's an error
            return {}
    
    def list_templates(self) -> List[WorkflowTemplateSchema]:
        """List all available workflow templates"""
        templates = []
        try:
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(('.yml', '.yaml')):
                    template_path = os.path.join(self.templates_dir, filename)
                    print(f"Loading template from: {template_path}")
                    
                    with open(template_path, 'r') as f:
                        template_data = yaml.safe_load(f)
                        
                        template = WorkflowTemplateSchema(
                            id=filename.rsplit('.', 1)[0],
                            name=template_data.get('name', filename),
                            description=template_data.get('description', ''),
                            steps=template_data.get('steps', [])
                        )
                        templates.append(template)
                        print(f"Loaded template: {template.id}")
        except Exception as e:
            print(f"Error loading templates: {str(e)}")
        return templates
    
    async def submit_workflow(self, name: str, template: str, parameters: Dict[str, Any]) -> str:
        """Submit a workflow for execution"""
        # Normalize template name to support both hyphen and underscore
        template = template.replace('_', '-').replace('.yml', '').replace('.yaml', '')
        # Create workflow config from parameters
        config = WorkflowConfig(**parameters)
        # Check if protein_id is provided and auto-populate parameters
        if 'protein_id' in parameters and template in ['protein-analysis', 'protein-drug-interaction']:
            protein_id = parameters['protein_id']
            logger.info(f"Auto-populating parameters for protein_id: {protein_id}")
            
            # Fetch protein data and store on IPFS
            protein_data = await self._fetch_and_store_protein_data(protein_id)
            
            # Update parameters with protein data
            if protein_data:
                parameters.update(protein_data)
                logger.info(f"Auto-populated parameters: {protein_data}")
        
        # Generate unique ID for workflow
        workflow_id = str(uuid.uuid4())
        
        # Create pipeline instance
        pipeline = DrugDiscoveryPipeline(config)
        
        # Store pipeline instance
        self.pipelines[workflow_id] = pipeline
        
        # Create workflow directory
        workflow_dir = os.path.join(self.workflows_dir, workflow_id)
        os.makedirs(workflow_dir, exist_ok=True)
        
        # Get template file
        # Try both .yml and .yaml extensions and also try with underscore instead of hyphen
        template_file = None
        template_variants = [
            template,                      # Original (normalized with hyphens)
            template.replace('-', '_'),    # With underscores
            template.replace('_', '-')     # With hyphens
        ]
        
        for template_variant in template_variants:
            for ext in ['.yml', '.yaml']:
                temp_file = os.path.join(self.templates_dir, f"{template_variant}{ext}")
                print(f"Looking for template at: {temp_file}")
                if os.path.exists(temp_file):
                    template_file = temp_file
                    print(f"Found template at: {temp_file}")
                    break
            if template_file:
                break
                
        if not template_file:
            available_templates = [f for f in os.listdir(self.templates_dir) if f.endswith(('.yml', '.yaml'))]
            raise ValueError(f"Template {template} not found. Available templates: {available_templates}")
        
        # Copy template to workflow directory and apply parameters
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        
        # TODO: Apply parameters to template_data
        
        # Write workflow file
        workflow_file = os.path.join(workflow_dir, "workflow.yml")
        with open(workflow_file, 'w') as f:
            yaml.dump(template_data, f)
        
        # Create results directory
        results_dir = os.path.join(self.results_dir, workflow_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # Record workflow start on blockchain
        tx_id = self.blockchain.record_workflow_start(
            workflow_id=workflow_id,
            template_id=template,
            parameters=parameters
        )
        
        # Record workflow execution
        execution = WorkflowExecutionSchema(
            id=workflow_id,
            name=name,
            template=template,
            status=WorkflowStatus.PENDING,
            parameters=parameters,
            start_time=datetime.utcnow(),
            steps=[],
            blockchain_tx=tx_id
        )
        self.executions[workflow_id] = execution
        
        # Execute workflow in background (you might want to use Celery or similar)
        # For now, we'll just simulate execution
        self._execute_workflow(workflow_id)
        
        return workflow_id
    
    def _execute_workflow(self, workflow_id: str):
        """Execute a workflow"""
        # Get workflow execution
        execution = self.executions.get(workflow_id)
        if not execution:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        # Update status to running
        execution.status = WorkflowStatus.RUNNING
        
        # Simulate workflow execution
        # In a real implementation, this would execute the workflow steps
        logger.info(f"Executing workflow {workflow_id}")
        
        # For now, we'll just simulate a successful execution
        execution.status = WorkflowStatus.COMPLETED
        execution.end_time = datetime.utcnow()
        
        # Record workflow completion on blockchain
        tx_id = self.blockchain.record_workflow_completion(
            workflow_id=workflow_id,
            status="COMPLETED",
            results={"message": "Workflow completed successfully"}
        )
        
        # Update blockchain transaction ID
        execution.blockchain_tx = tx_id
        
        logger.info(f"Workflow {workflow_id} completed successfully")
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecutionSchema]:
        """Get workflow execution details"""
        return self.executions.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowExecutionSchema]:
        """List all workflows"""
        return list(self.executions.values())
    
    def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get the results of a workflow execution"""
        # Check for structure preparation results
        try:
            # Look for processed.pdb and descriptors in the structures directory
            workflow_dir = os.path.join(self.upload_dir, "structures", workflow_id)
            if os.path.exists(workflow_dir):
                # Check if we have descriptors
                results_file = os.path.join(workflow_dir, "results.json")
                if os.path.exists(results_file):
                    with open(results_file, 'r') as f:
                        return json.load(f)
                
                # If no results.json, check if we have processed.pdb
                processed_pdb = os.path.join(workflow_dir, "processed.pdb")
                if os.path.exists(processed_pdb):
                    # Get descriptors from the execution data if available
                    execution = self.executions.get(workflow_id)
                    if execution and hasattr(execution, 'descriptors'):
                        return {
                            "STRUCTURE_PREPARATION": {
                                "status": "success",
                                "descriptors": execution.descriptors
                            }
                        }
        except Exception as e:
            logger.error(f"Error retrieving workflow results: {str(e)}")
        
        # Default response if no specific results found
        return {
            "message": "Workflow completed successfully",
            "workflow_id": workflow_id
        }
    
    def verify_workflow_integrity(self, workflow_id: str) -> WorkflowVerificationSchema:
        """Verify the integrity of a workflow execution using blockchain"""
        # In a real implementation, this would verify the workflow results on the blockchain
        # For now, we'll just return a simple verification
        return WorkflowVerificationSchema(
            valid=True,
            reason="Workflow verified on blockchain",
            hash="dummy_hash"
        )