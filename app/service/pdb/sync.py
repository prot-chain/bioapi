from .fetch import PDBFetchService


class PDBSyncService:
    """
    Service to handle syncing parsed protein data with the blockchain.
    """

    def __init__(self):
        self.fetch_service = PDBFetchService()

    def sync_with_blockchain(self, protein_id: str) -> str:
        """
        Sync parsed protein data with the blockchain.

        Args:
            protein_id (str): The PDB ID of the protein.

        Returns:
            str: Status of the synchronization.
        """
        try:
            raw_data = self.fetch_service.fetch_protein_data(protein_id)
            _ = self.fetch_service.parse_protein_data(raw_data)
            # Placeholder for blockchain sync logic
            # sending parsed_data to a blockchain API
            return "Synchronization successful"
        except Exception as e:
            raise Exception(f"Failed to sync protein data for ID {protein_id}: {e}")
