from .endpoints import protein

from fastapi import APIRouter

router = APIRouter()
router.include_router(protein.router, prefix="/protein", tags=["uniprot"])
