from fastapi import APIRouter

# Use relative imports instead of absolute
from . import protein  # Import existing endpoints
from . import workflow  # Import the new workflow endpoints
