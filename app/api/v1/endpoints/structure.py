from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from app.core.config import get_config
from app.core.structure_prep import StructurePreparation

router = APIRouter()

class StructureRequest(BaseModel):
    file_path: str

@router.post("/workflows/{workflow_id}/structure")
async def process_structure(workflow_id: str, request: StructureRequest):
    try:
        config = get_config()
        prep = StructurePreparation(str(Path(config.upload_dir) / "structures"))
        result = prep.prepare_structure(request.file_path, workflow_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
        
        if result["status"] == "error":
            print(f"Error processing structure: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        
        print(f"Successfully processed structure for workflow {workflow_id}")
        return result
    except Exception as e:
        print(f"Unexpected error processing structure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
