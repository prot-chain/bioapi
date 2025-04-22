from .endpoints import protein
from .endpoints import workflow
from .endpoints import direct_binding
from . import auth  # Import the new auth module

from fastapi import APIRouter
from .endpoints import structure

router = APIRouter()
router.include_router(structure.router)
router.include_router(protein.router, prefix="/protein", tags=["protein"])
router.include_router(workflow.router, prefix="/workflows", tags=["workflows"])
router.include_router(direct_binding.router, tags=["binding-site"])
router.include_router(auth.router, tags=["auth"])  # Include the auth router
