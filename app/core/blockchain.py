import os
import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlockchainClient:
    """Client for interacting with Hyperledger Fabric blockchain"""
    
    def __init__(self):
        """Initialize blockchain client"""
        # Path to connection profile
        self.config_path = os.getenv("FABRIC_CONFIG_PATH", "/config/connection-profile.json")
        
        # Channel and chaincode info
        self.channel_name = os.getenv("FABRIC_CHANNEL", "protochannel")
        self.chaincode_name = os.getenv("FABRIC_CHAINCODE", "workflow-chaincode")
        
        # Organization and user info
        self.org_name = os.getenv("FABRIC_ORG", "org1.example.com")
        self.user_name = os.getenv("FABRIC_USER", "Admin")
        
        # Check if we can use the Fabric SDK
        try:
            from hfc.fabric import Client as FabricClient
            self.fabric_available = True
        except ImportError:
            logger.warning("Hyperledger Fabric SDK not installed. Using mock implementation.")
            self.fabric_available = False
        
        # Initialize client if fabric SDK is available
        self.client = None
        if self.fabric_available:
            try:
                self._init_fabric_client()
            except Exception as e:
                logger.error(f"Failed to initialize Fabric client: {str(e)}")
                # Fall back to mock mode
                self.fabric_available = False
        
        # In development mode, use a local file to simulate blockchain
        self.mock_mode = not self.fabric_available
        
        if self.mock_mode:
            logger.warning("Using mock blockchain implementation")
            # Create a local file to simulate blockchain for development
            self.mock_ledger_file = os.path.join(settings.data_dir, "mock_ledger.json")
            os.makedirs(os.path.dirname(self.mock_ledger_file), exist_ok=True)
            if not os.path.exists(self.mock_ledger_file):
                with open(self.mock_ledger_file, "w") as f:
                    json.dump({"transactions": []}, f)
    
    def _init_fabric_client(self):
        """Initialize the Hyperledger Fabric client"""
        from hfc.fabric import Client as FabricClient
        
        # Create client instance
        self.client = FabricClient(net_profile=self.config_path)
        
        # Set up crypto suite
        crypto = self.client.get_crypto_suite()
        self.client.set_crypto_suite(crypto)
        
        # Enroll user
        self.client.get_user(org_name=self.org_name, name=self.user_name)
    
    def compute_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file"""
        if not os.path.exists(file_path):
            return ""
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _mock_transaction(self, function_name: str, args: Dict[str, Any]) -> str:
        """Simulate a blockchain transaction for development"""
        # Generate a mock transaction ID
        tx_id = hashlib.sha256(f"{function_name}-{time.time()}-{json.dumps(args)}".encode()).hexdigest()
        
        # Load the mock ledger
        with open(self.mock_ledger_file, "r") as f:
            ledger = json.load(f)
        
        # Append transaction
        ledger["transactions"].append({
            "tx_id": tx_id,
            "timestamp": time.time(),
            "function": function_name,
            "args": args
        })
        
        # Save updated ledger
        with open(self.mock_ledger_file, "w") as f:
            json.dump(ledger, f, indent=2)
        
        logger.info(f"Mock transaction recorded: {function_name} ({tx_id})")
        return tx_id
    
    def _invoke_chaincode(self, function_name: str, args: Dict[str, Any]) -> str:
        """Invoke chaincode on the blockchain"""
        if self.mock_mode:
            return self._mock_transaction(function_name, args)
        
        try:
            # Import Fabric module within function to avoid import errors
            from hfc.fabric import Client as FabricClient
            
            # Convert args to array format expected by chaincode
            args_array = [json.dumps(args)]
            
            # Create transaction proposal
            tx_context = self.client.tx_context(self.user_name, self.org_name)
            
            # Send transaction proposal
            response = self.client.chaincode_invoke(
                requestor=self.user_name,
                channel_name=self.channel_name,
                peer_names=[f"peer0.{self.org_name}"],
                args=args_array,
                cc_name=self.chaincode_name,
                fcn=function_name,
                tx_context=tx_context
            )
            
            # Return transaction ID
            return tx_context.tx_id
            
        except Exception as e:
            logger.error(f"Chaincode invocation failed: {str(e)}")
            # Fall back to mock transaction for development
            return self._mock_transaction(function_name, args)
    
    def record_workflow_start(
        self, 
        workflow_id: str, 
        template_id: str, 
        parameters: Dict[str, Any]
    ) -> str:
        """Record the start of a workflow execution on the blockchain"""
        args = {
            "workflowId": workflow_id,
            "templateId": template_id,
            "timestamp": int(time.time()),
            "parameters": parameters
        }
        
        return self._invoke_chaincode("recordWorkflowStart", args)
    
    def record_workflow_step(
        self, 
        workflow_id: str, 
        step_id: str, 
        status: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record a workflow step on the blockchain"""
        args = {
            "workflowId": workflow_id,
            "stepId": step_id,
            "status": status,
            "timestamp": int(time.time()),
            "details": details or {}
        }
        
        return self._invoke_chaincode("recordWorkflowStep", args)
    
    def record_workflow_completion(
        self, 
        workflow_id: str, 
        status: str, 
        results: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> str:
        """Record the completion of a workflow execution on the blockchain"""
        args = {
            "workflowId": workflow_id,
            "status": status,
            "timestamp": int(time.time()),
            "results": results or {},
            "error": error or ""
        }
        
        return self._invoke_chaincode("recordWorkflowCompletion", args)
    
    def _mock_verification(self, workflow_id: str, output_hash: str) -> bool:
        """Simulate verification in mock mode"""
        with open(self.mock_ledger_file, "r") as f:
            ledger = json.load(f)
        
        # Find the completion record for this workflow
        for tx in reversed(ledger["transactions"]):
            if (tx["function"] == "recordWorkflowCompletion" and 
                tx["args"]["workflowId"] == workflow_id):
                # Check if output hash matches
                return tx["args"].get("outputHash", "") == output_hash
        
        return False
    
    def verify_workflow_integrity(self, workflow_id: str, output_hash: str) -> bool:
        """Verify the integrity of workflow results using blockchain records"""
        if self.mock_mode:
            # In mock mode, just simulate verification
            return self._mock_verification(workflow_id, output_hash)
        
        try:
            # Import Fabric module within function to avoid import errors
            from hfc.fabric import Client as FabricClient
            
            # Query chaincode to verify workflow output
            args_array = [workflow_id, output_hash]
            
            response = self.client.chaincode_query(
                requestor=self.user_name,
                channel_name=self.channel_name,
                peers=[f"peer0.{self.org_name}"],
                args=args_array,
                cc_name=self.chaincode_name,
                fcn="verifyWorkflowIntegrity"
            )
            
            # Parse response
            result = json.loads(response.decode('utf-8'))
            return result.get("valid", False)
            
        except Exception as e:
            logger.error(f"Chaincode query failed: {str(e)}")
            # Fall back to mock verification
            return self._mock_verification(workflow_id, output_hash)