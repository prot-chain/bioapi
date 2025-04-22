from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING" 
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class WorkflowStepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class WorkflowStep(BaseModel):
    id: str
    status: WorkflowStepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    blockchain_tx: Optional[str] = None  # Add blockchain transaction ID

class WorkflowSubmissionSchema(BaseModel):
    name: str
    template: str
    parameters: Dict[str, Any] = {}

class WorkflowExecutionSchema(BaseModel):
    id: str
    name: str
    template: str
    status: WorkflowStatus
    parameters: Dict[str, Any] = {}
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[WorkflowStep] = []
    results_url: Optional[str] = None
    blockchain_tx: Optional[str] = None  # Add blockchain transaction ID

class WorkflowTemplateSchema(BaseModel):
    id: str
    name: str
    description: str
    parameters_schema: Dict[str, Any] = {}

class WorkflowVerificationSchema(BaseModel):
    valid: bool
    reason: str
    hash: Optional[str] = None