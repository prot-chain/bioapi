from fastapi import APIRouter

from .endpoints import protein
from .endpoints import workflow
from .endpoints import direct_binding
from .endpoints import structure
from . import auth

router = APIRouter(prefix="/api/v1")

# Include all routers
# router.include_router(structure.router) # Temporarily commented out
router.include_router(protein.router, prefix="/protein", tags=["protein"]) # Activate protein endpoints
router.include_router(workflow.router, prefix="/workflows", tags=["workflows"])
# router.include_router(direct_binding.router) # Temporarily commented out
# router.include_router(auth.router) # Temporarily commented out
