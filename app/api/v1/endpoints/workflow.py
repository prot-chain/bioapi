from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import yaml
from enum import Enum
import json

from app.schema.workflow import (
    WorkflowStatus,
    WorkflowStepStatus,
    WorkflowStep,
    WorkflowExecutionSchema,
    WorkflowTemplateSchema,
    WorkflowSubmissionSchema,
    WorkflowVerificationSchema
)
from app.service.workflow.engine import WorkflowEngine
from app.core.binding_site import BindingSiteAnalysis
from app.core.structure_prep import StructurePreparation

# Create router
router = APIRouter()

# Create workflow engine instance
workflow_engine = WorkflowEngine()

# Create binding site analysis instance
upload_dir = os.environ.get('UPLOAD_DIR', 'uploads')
binding_site_analyzer = BindingSiteAnalysis(upload_dir)
structure_prep = StructurePreparation(upload_dir)

@router.get("/templates", response_model=List[Dict])
async def list_workflow_templates():
    """List available workflow templates"""
    templates = workflow_engine.list_templates()
    # Convert Pydantic models to dictionaries
    return [template.dict() for template in templates]

@router.post("", response_model=Dict[str, Any])
async def submit_workflow(submission: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Submit a new workflow for execution
    
    If protein_id is provided, the following parameters will be auto-populated:
    - protein_name: Name of the protein
    - protein_ipfs_cid: IPFS CID of the protein data
    - protein_sequence: Amino acid sequence of the protein
    - pdb_link: Link to the PDB file (if available)
    """
    try:
        if not submission.get("name"):
            raise ValueError("Workflow name is required")
        if not submission.get("template"):
            raise ValueError("Template name is required")
            
        workflow_id = await workflow_engine.submit_workflow(
            name=submission.get("name"),
            template=submission.get("template"),
            parameters=submission.get("parameters", {})
        )
        return {"id": workflow_id, "message": "Workflow submitted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error submitting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[Dict])
async def list_workflows():
    """List all workflows"""
    workflows = workflow_engine.list_workflows()
    # Convert Pydantic models to dictionaries
    return [workflow.dict() for workflow in workflows]

@router.get("/{workflow_id}/status", response_model=Dict)
async def get_workflow_status(workflow_id: str):
    """Check the status of a workflow execution"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": workflow.id,
        "status": workflow.status,
        "start_time": workflow.start_time,
        "end_time": workflow.end_time,
        "blockchain_tx": workflow.blockchain_tx
    }

@router.get("/{workflow_id}/results", response_model=Dict)
async def get_workflow_results(workflow_id: str):
    """Retrieve the results of a workflow execution"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow.status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Workflow not completed. Current status: {workflow.status}")
        
    results = workflow_engine.get_workflow_results(workflow_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
        
    return results

@router.get("/{workflow_id}/verify", response_model=Dict)
async def verify_workflow_integrity(workflow_id: str):
    """Verify the integrity of workflow results using blockchain"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    verification = workflow_engine.verify_workflow_integrity(workflow_id)
    return verification.dict()

@router.get("/{workflow_id}", response_model=Dict)
async def get_workflow(workflow_id: str):
    """Get details of a specific workflow execution"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@router.post("/{workflow_id}/binding-site-analysis", response_model=Dict)
async def run_binding_site_analysis(workflow_id: str, background_tasks: BackgroundTasks):
    """Run binding site analysis on a processed structure"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow.status != WorkflowStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Workflow must be completed to run binding site analysis. Current status: {workflow.status}"
        )
    
    # Check if structure preparation was successful
    results = workflow_engine.get_workflow_results(workflow_id)
    if not results or "STRUCTURE_PREPARATION" not in results or results["STRUCTURE_PREPARATION"].get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail="Structure preparation results not found or unsuccessful"
        )
    
    # Run binding site analysis in background
    background_tasks.add_task(binding_site_analyzer.analyze_binding_sites, workflow_id)
    
    return {
        "status": "success",
        "message": "Binding site analysis started",
        "workflow_id": workflow_id
    }

@router.get("/{workflow_id}/binding-sites", response_model=Dict)
async def get_binding_sites(workflow_id: str):
    """Get binding site analysis results"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check if results exist
    results = workflow_engine.get_workflow_results(workflow_id)
    if not results or "BINDING_SITE_ANALYSIS" not in results:
        raise HTTPException(
            status_code=404,
            detail="Binding site analysis results not found"
        )
    
    return results["BINDING_SITE_ANALYSIS"]

@router.delete("/{workflow_id}", response_model=Dict)
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow.status not in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel workflow with status {workflow.status}"
        )
    
    # Try to cancel the workflow if the engine supports it
    if hasattr(workflow_engine, 'cancel_workflow'):
        try:
            workflow_engine.cancel_workflow(workflow_id)
            return {"id": workflow_id, "message": "Workflow cancelled successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=501, detail="Workflow cancellation not implemented")
