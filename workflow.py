from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid
import subprocess
import yaml
from enum import Enum
import json
import time

# Define models
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

class WorkflowStep:
    def __init__(
        self,
        id: str,
        status: WorkflowStepStatus,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        output: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.id = id
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.output = output
        self.error = error
    
    def dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "output": self.output,
            "error": self.error
        }

class WorkflowExecution:
    def __init__(
        self,
        id: str,
        name: str,
        template: str,
        status: WorkflowStatus,
        parameters: Dict[str, Any] = {},
        start_time: datetime = None,
        end_time: Optional[datetime] = None,
        steps: List[WorkflowStep] = None,
        results_url: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.template = template
        self.status = status
        self.parameters = parameters
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time
        self.steps = steps or []
        self.results_url = results_url
    
    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "status": self.status,
            "parameters": self.parameters,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [step.dict() for step in self.steps],
            "results_url": self.results_url
        }
    
    def to_json(self):
        return json.dumps(self.dict())
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        steps = []
        for step_data in data.get("steps", []):
            step = WorkflowStep(
                id=step_data["id"],
                status=step_data["status"],
                start_time=datetime.fromisoformat(step_data["start_time"]) if step_data.get("start_time") else None,
                end_time=datetime.fromisoformat(step_data["end_time"]) if step_data.get("end_time") else None,
                output=step_data.get("output"),
                error=step_data.get("error")
            )
            steps.append(step)
        
        return cls(
            id=data["id"],
            name=data["name"],
            template=data["template"],
            status=data["status"],
            parameters=data.get("parameters", {}),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            steps=steps,
            results_url=data.get("results_url")
        )

# Workflow engine
class WorkflowEngine:
    def __init__(self):
        # Create required directories
        self.workflows_dir = "/app/data/workflows"
        self.templates_dir = "/app/data/templates"
        self.results_dir = "/app/data/workflow_results"
        self.state_dir = "/app/data/workflow_state"
        self.workflow_binary = "/app/bin/protchainworkflow"
        
        # Ensure directories exist
        os.makedirs(self.workflows_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.state_dir, exist_ok=True)
        
        # Load existing executions
        self.executions = self._load_executions()
    
    def _load_executions(self):
        """Load existing workflow executions from state files"""
        executions = {}
        if os.path.exists(self.state_dir):
            for filename in os.listdir(self.state_dir):
                if filename.endswith('.json'):
                    workflow_id = filename.rsplit('.', 1)[0]
                    try:
                        with open(os.path.join(self.state_dir, filename), 'r') as f:
                            execution = WorkflowExecution.from_json(f.read())
                            executions[workflow_id] = execution
                    except Exception as e:
                        print(f"Error loading workflow {workflow_id}: {str(e)}")
        return executions
    
    def _save_execution(self, execution):
        """Save workflow execution state to a file"""
        state_file = os.path.join(self.state_dir, f"{execution.id}.json")
        with open(state_file, 'w') as f:
            f.write(execution.to_json())
    
    def list_templates(self) -> List[Dict]:
        """List all available workflow templates"""
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(('.yml', '.yaml')):
                template_id = filename.rsplit('.', 1)[0]
                try:
                    with open(os.path.join(self.templates_dir, filename), 'r') as f:
                        template_data = yaml.safe_load(f) or {}
                        
                        template = {
                            "id": template_id,
                            "name": template_data.get('name', template_id),
                            "description": template_data.get('description', ''),
                            "parameters_schema": template_data.get('parameters', {})
                        }
                        templates.append(template)
                except Exception as e:
                    print(f"Error reading template {filename}: {str(e)}")
        return templates
    
    def submit_workflow(self, name: str, template: str, parameters: Dict[str, Any], background_tasks: BackgroundTasks) -> str:
        """Submit a workflow for execution"""
        # Generate unique ID for workflow
        workflow_id = str(uuid.uuid4())
        
        # Create workflow directory
        workflow_dir = os.path.join(self.workflows_dir, workflow_id)
        os.makedirs(workflow_dir, exist_ok=True)
        
        # Get template file
        template_file = os.path.join(self.templates_dir, f"{template}.yml")
        if not os.path.exists(template_file):
            raise ValueError(f"Template {template} not found")
        
        # Copy template to workflow directory
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f) or {}
        
        # Apply parameters to template
        self._apply_parameters(template_data, parameters)
        
        # Write workflow file
        workflow_file = os.path.join(workflow_dir, "workflow.yml")
        with open(workflow_file, 'w') as f:
            yaml.dump(template_data, f)
        
        # Create results directory
        results_dir = os.path.join(self.results_dir, workflow_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # Record workflow execution
        execution = WorkflowExecution(
            id=workflow_id,
            name=name,
            template=template,
            status=WorkflowStatus.PENDING,
            parameters=parameters,
            start_time=datetime.utcnow()
        )
        self.executions[workflow_id] = execution
        self._save_execution(execution)
        
        # Execute workflow in background
        background_tasks.add_task(
            self._execute_workflow,
            workflow_id,
            workflow_file,
            results_dir
        )
        
        return workflow_id
    
    def _apply_parameters(self, template_data, parameters):
        """Apply user parameters to the template"""
        # This is a simple implementation - in a real system you'd want more robust parameter handling
        for key, value in parameters.items():
            # Handle process command parameter replacement
            for step in template_data.get('steps', []):
                if 'process' in step:
                    step['process'] = step['process'].replace(f'${{{key}}}', str(value))
                    step['process'] = step['process'].replace(f'${{parameters.{key}}}', str(value))
    
    def _execute_workflow(self, workflow_id: str, workflow_file: str, results_dir: str):
        """Execute a workflow using the workflow engine binary"""
        # Update status to running
        execution = self.executions.get(workflow_id)
        if not execution:
            print(f"Workflow {workflow_id} not found")
            return
            
        execution.status = WorkflowStatus.RUNNING
        self._save_execution(execution)
        
        try:
            # For testing without blockchain, use a simple subprocess instead
            cmd = [
                "bash", "-c", 
                f"mkdir -p {results_dir}/test && echo 'Hello, {execution.name}!' > {results_dir}/test/output.txt"
            ]
            
            print(f"Executing command: {' '.join(cmd)}")
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Process output
            stdout, stderr = process.communicate()
            
            # Update workflow status based on result
            if process.returncode == 0:
                execution.status = WorkflowStatus.COMPLETED
                execution.end_time = datetime.utcnow()
                execution.results_url = f"/api/v1/workflows/{workflow_id}/results"
                
                # Add successful step
                step = WorkflowStep(
                    id="main",
                    status=WorkflowStepStatus.COMPLETED,
                    start_time=execution.start_time,
                    end_time=datetime.utcnow(),
                    output=stdout + "\nSuccessfully executed mock workflow step"
                )
                execution.steps.append(step)
            else:
                execution.status = WorkflowStatus.FAILED
                execution.end_time = datetime.utcnow()
                
                # Add failed step
                step = WorkflowStep(
                    id="main",
                    status=WorkflowStepStatus.FAILED,
                    start_time=execution.start_time,
                    end_time=datetime.utcnow(),
                    error=stderr
                )
                execution.steps.append(step)
            
            # Save updated execution state
            self._save_execution(execution)
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.utcnow()
            
            # Add error step
            step = WorkflowStep(
                id="main",
                status=WorkflowStepStatus.FAILED,
                start_time=execution.start_time,
                end_time=datetime.utcnow(),
                error=str(e)
            )
            execution.steps.append(step)
            
            # Save updated execution state
            self._save_execution(execution)
            
            print(f"Error executing workflow {workflow_id}: {str(e)}")
    
    def _parse_steps_from_output(self, execution, output):
        """Parse workflow steps from the output log"""
        # This is a simple implementation that looks for specific patterns in the output
        # In a real system, you would want a more structured approach
        lines = output.split('\n')
        current_step = None
        step_start_time = None
        
        for line in lines:
            if "Executing step:" in line:
                # Start of a new step
                step_id = line.split("Executing step:")[1].strip()
                current_step = step_id
                step_start_time = datetime.utcnow()
            
            if current_step and "Submitting transaction: completeStep" in line:
                # End of a step
                step = WorkflowStep(
                    id=current_step,
                    status=WorkflowStepStatus.COMPLETED,
                    start_time=step_start_time,
                    end_time=datetime.utcnow(),
                    output=f"Step {current_step} completed"
                )
                execution.steps.append(step)
                current_step = None
                step_start_time = None
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow execution details"""
        execution = self.executions.get(workflow_id)
        return execution.dict() if execution else None
    
    def list_workflows(self) -> List[Dict]:
        """List all workflow executions"""
        return [execution.dict() for execution in self.executions.values()]
    
    def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution results"""
        if workflow_id not in self.executions:
            return None
            
        results_dir = os.path.join(self.results_dir, workflow_id)
        if not os.path.exists(results_dir):
            return {"error": "Results not found"}
            
        # Gather results from the results directory
        results = {}
        for root, dirs, files in os.walk(results_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, results_dir)
                try:
                    with open(file_path, 'r') as f:
                        results[rel_path] = f.read()
                except:
                    results[rel_path] = "Binary file - cannot display content"
                        
        return results

# Singleton instance of the workflow engine
workflow_engine = WorkflowEngine()

# Router
router = APIRouter()

@router.get("/templates", response_model=List[Dict])
async def list_workflow_templates():
    """List available workflow templates"""
    return workflow_engine.list_templates()

@router.post("", response_model=Dict)
async def submit_workflow(submission: Dict[str, Any], background_tasks: BackgroundTasks):
    """Submit a new workflow for execution"""
    try:
        if not submission.get("name"):
            raise ValueError("Workflow name is required")
        if not submission.get("template"):
            raise ValueError("Template name is required")
            
        workflow_id = workflow_engine.submit_workflow(
            name=submission.get("name"),
            template=submission.get("template"),
            parameters=submission.get("parameters", {}),
            background_tasks=background_tasks
        )
        return {"id": workflow_id, "message": "Workflow submitted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error submitting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[Dict])
async def list_workflows():
    """List all workflows"""
    return workflow_engine.list_workflows()

@router.get("/{workflow_id}/status", response_model=Dict)
async def get_workflow_status(workflow_id: str):
    """Check the status of a workflow execution"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": workflow["id"],
        "status": workflow["status"],
        "start_time": workflow["start_time"],
        "end_time": workflow["end_time"]
    }

@router.get("/{workflow_id}/results", response_model=Dict)
async def get_workflow_results(workflow_id: str):
    """Retrieve the results of a workflow execution"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    if workflow["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Workflow not completed. Current status: {workflow['status']}")
        
    results = workflow_engine.get_workflow_results(workflow_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
        
    return results

@router.get("/{workflow_id}", response_model=Dict)
async def get_workflow(workflow_id: str):
    """Get details of a specific workflow execution"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
