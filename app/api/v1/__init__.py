from .endpoints import protein
from .endpoints import workflow

from fastapi import APIRouter

router = APIRouter()
router.include_router(protein.router, prefix="/protein", tags=["uniprot"])
router.include_router(workflow.router, prefix="/workflows", tags=["workflows"])
