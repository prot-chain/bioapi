from .endpoints import pdb

from fastapi import APIRouter

router = APIRouter()
router.include_router(pdb.router, prefix="/pdb", tags=["pdb"])
