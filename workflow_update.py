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
