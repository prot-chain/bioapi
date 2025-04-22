from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import os
from pathlib import Path
import tempfile
import shutil
import time

from app.core.binding_site import BindingSiteAnalysis

# Create router
router = APIRouter()

# Create binding site analysis instance
upload_dir = os.environ.get('UPLOAD_DIR', 'uploads')
binding_site_analyzer = BindingSiteAnalysis(upload_dir)

# Helper function to run binding site analysis and clean up temporary files
def run_binding_site_analysis_and_cleanup(analyzer, workflow_id, pdb_path, output_dir, tmp_dir):
    try:
        # Ensure the PDB file exists before analysis
        if not os.path.exists(pdb_path):
            print(f"ERROR: PDB file not found at {pdb_path}")
            return
            
        print(f"Starting binding site analysis for {workflow_id} with PDB file: {pdb_path}")
        # Run the binding site analysis
        result = analyzer.analyze_binding_sites_direct(workflow_id, pdb_path, output_dir)
        print(f"Binding site analysis completed for {workflow_id}: {result}")
    except Exception as e:
        print(f"Error in binding site analysis: {str(e)}")
    finally:
        # Clean up the temporary directory after a delay to ensure all processes are done
        time.sleep(2)
        try:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
                print(f"Cleaned up temporary directory: {tmp_dir}")
        except Exception as cleanup_error:
            print(f"Error cleaning up temporary directory: {str(cleanup_error)}")

@router.post("/direct-binding-analysis", response_model=Dict[str, Any])
async def direct_binding_analysis(data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Direct endpoint for binding site analysis that bypasses workflow checks
    
    This endpoint accepts the PDB content and structure data directly,
    allowing for binding site analysis without workflow registration.
    """
    try:
        workflow_id = data.get("workflow_id")
        if not workflow_id:
            raise HTTPException(status_code=400, detail="workflow_id is required")
        
        pdb_content = data.get("pdb_content")
        if not pdb_content:
            raise HTTPException(status_code=400, detail="pdb_content is required")
        
        # Get path information - simplified approach
        wsl_path = data.get("wsl_path")
        
        print(f"Direct binding analysis for workflow {workflow_id}")
        print(f"Using WSL path: {wsl_path}")
        
        # Create a persistent temporary directory that won't be deleted
        tmp_dir = tempfile.mkdtemp(prefix=f"binding_site_{workflow_id}_")
        tmp_pdb_path = os.path.join(tmp_dir, "processed.pdb")
        
        # Write the PDB content to the temporary file
        with open(tmp_pdb_path, "w") as f:
            f.write(pdb_content)
        
        print(f"Wrote PDB content to persistent temporary file: {tmp_pdb_path}")
        
        # Run binding site analysis in background with simplified parameters
        # The background task will clean up the temporary directory when done
        background_tasks.add_task(
            run_binding_site_analysis_and_cleanup, 
            binding_site_analyzer,
            workflow_id, 
            tmp_pdb_path,
            wsl_path,
            tmp_dir
        )
        
        print(f"Started binding site analysis in background for workflow {workflow_id}")
        
        return {
            "status": "success",
            "message": "Direct binding site analysis started",
            "workflow_id": workflow_id
        }
    except Exception as e:
        print(f"Error in direct binding analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in direct binding analysis: {str(e)}")
