import os
import uuid
import subprocess
import yaml
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.schema.workflow import (
    WorkflowExecutionSchema, 
    WorkflowStatus, 
    WorkflowTemplateSchema, 
    WorkflowStep,
    WorkflowStepStatus
)

class WorkflowEngine:
    def __init__(self):
        # Create required directories
        self.workflows_dir = os.path.join(settings.DATA_DIR, "workflows")
        self.templates_dir = os.path.join(settings.DATA_DIR, "templates")
        self.results_dir = os.path.join(settings.DATA_DIR, "workflow_results")
        self.workflow_binary = settings.WORKFLOW_BINARY_PATH
        
        # In-memory storage for workflows (replace with database in production)
        self.executions = {}
        
        # Ensure directories exist
        os.makedirs(self.workflows_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
    
    def list_templates(self) -> List[WorkflowTemplateSchema]:
        """List all available workflow templates"""
        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(('.yml', '.yaml')):
                with open(os.path.join(self.templates_dir, filename), 'r') as f:
                    template_data = yaml.safe_load(f)
                    
                    template = WorkflowTemplateSchema(
                        id=filename.rsplit('.', 1)[0],
                        name=template_data.get('name', filename),
                        description=template_data.get('description', ''),
                        parameters_schema=template_data.get('parameters', {})
                    )
                    templates.append(template)
        return templates
    
    def submit_workflow(self, name: str, template: str, parameters: Dict[str, Any]) -> str:
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
        
        # Copy template to workflow directory and apply parameters
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        
        # TODO: Apply parameters to template_data
        
        # Write workflow file
        workflow_file = os.path.join(workflow_dir, "workflow.yml")
        with open(workflow_file, 'w') as f:
            yaml.dump(template_data, f)
        
        # Create results directory
        results_dir = os.path.join(self.results_dir, workflow_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # Record workflow execution
        execution = WorkflowExecutionSchema(
            id=workflow_id,
            name=name,
            template=template,
            status=WorkflowStatus.PENDING,
            parameters=parameters,
            start_time=datetime.utcnow(),
            steps=[]
        )
        self.executions[workflow_id] = execution
        
        # Execute workflow in background (you might want to use Celery or similar)
        # For simplicity, we'll execute it directly here
        self._execute_workflow(workflow_id, workflow_file, results_dir)
        
        return workflow_id
    
    def _execute_workflow(self, workflow_id: str, workflow_file: str, results_dir: str):
        """Execute a workflow using the workflow engine binary"""
        # Update status to running
        self.executions[workflow_id].status = WorkflowStatus.RUNNING
        
        try:
            # Execute workflow binary
            cmd = [
                self.workflow_binary,
                "-workflow", workflow_file,
                "-workdir", results_dir,
                "-chaincode", "proteomic"  # Use your existing chaincode
            ]
            
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
                self.executions[workflow_id].status = WorkflowStatus.COMPLETED
                self.executions[workflow_id].end_time = datetime.utcnow()
                self.executions[workflow_id].results_url = f"/api/v1/workflows/{workflow_id}/results"
                
                # Add successful step
                step = WorkflowStep(
                    id="main",
                    status=WorkflowStepStatus.COMPLETED,
                    start_time=self.executions[workflow_id].start_time,
                    end_time=datetime.utcnow(),
                    output=stdout
                )
                self.executions[workflow_id].steps.append(step)
            else:
                self.executions[workflow_id].status = WorkflowStatus.FAILED
                self.executions[workflow_id].end_time = datetime.utcnow()
                
                # Add failed step
                step = WorkflowStep(
                    id="main",
                    status=WorkflowStepStatus.FAILED,
                    start_time=self.executions[workflow_id].start_time,
                    end_time=datetime.utcnow(),
                    error=stderr
                )
                self.executions[workflow_id].steps.append(step)
        except Exception as e:
            self.executions[workflow_id].status = WorkflowStatus.FAILED
            self.executions[workflow_id].end_time = datetime.utcnow()
            
            # Add error step
            step = WorkflowStep(
                id="main",
                status=WorkflowStepStatus.FAILED,
                start_time=self.executions[workflow_id].start_time,
                end_time=datetime.utcnow(),
                error=str(e)
            )
            self.executions[workflow_id].steps.append(step)
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecutionSchema]:
        """Get workflow execution details"""
        return self.executions.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowExecutionSchema]:
        """List all workflow executions"""
        return list(self.executions.values())
    
    def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution results"""
        if workflow_id not in self.executions:
            return None
            
        results_dir = os.path.join(self.results_dir, workflow_id)
        if not os.path.exists(results_dir):
            return {"error": "Results not found"}
            
        # Gather results from the results directory
        results = {}
        for filename in os.listdir(results_dir):
            file_path = os.path.join(results_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    try:
                        results[filename] = f.read()
                    except:
                        results[filename] = "Binary file"
                        
        return results