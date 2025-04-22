from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from ..config import get_settings
from ...structure_prep import StructurePreparation

router = APIRouter()
settings = get_settings()

class StructureRequest(BaseModel):
    file_path: str

@router.post("/api/v1/workflows/{workflow_id}/structure")
async def process_structure(workflow_id: str, request: StructureRequest):
    try:
        prep = StructurePreparation(str(Path(settings.upload_dir) / "structures"))
        result = prep.prepare_structure(request.file_path, workflow_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
