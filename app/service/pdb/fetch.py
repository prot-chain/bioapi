from app.service.utils import pdb_file_download_link
from app.schema.pdb import PDBEntry
from app.schema.protein import EntryAudit, ProteinData
from httpx import AsyncClient


class PDBFetchService:
    """
    Service to handle fetching and parsing protein data from the PDB API.
    """

    BASE_URL = "https://data.rcsb.org/rest/v1/core/entry"

    async def fetch_protein_data(self, protein_id: str) -> PDBEntry:
        """
        Fetch raw protein data from the PDB API.

        Args:
            protein_id (str): The PDB ID of the protein.

        Returns:
            dict: Raw protein data.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        async with AsyncClient() as client:
            url = f"{self.BASE_URL}/{protein_id}"
            logger.info(f"Fetching protein data from: {url}")
            
            response = await client.get(url)
            logger.info(f"PDB API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"Failed to fetch protein data for ID {protein_id}. Status: {response.status_code}"
                if response.text:
                    error_msg += f". Response: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            try:
                json_data = response.json()
                logger.info(f"Successfully parsed JSON for protein {protein_id}")
                data = PDBEntry(**json_data)
                return data
            except Exception as e:
                error_msg = f"Failed to parse protein data for ID {protein_id}: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)

    async def parse_protein_data(self, data: PDBEntry) -> ProteinData:
        """
        Parse raw protein data into a structured format.

        Args:
            raw_data (dict): Raw protein data.

        Returns:
            dict: Parsed protein data.
        """
        protein_data = ProteinData(
            primary_accession=data.rcsb_entry_container_identifiers.entry_id,
            entry_audit=EntryAudit(
                first_public_date=data.rcsb_accession_info.initial_release_date,
                last_annotation_update_date=data.rcsb_accession_info.revision_date,
                sequence_version=data.rcsb_accession_info.major_revision,
                entry_version=data.rcsb_accession_info.minor_revision,
            ),
        )
        protein_data.pdb_link = pdb_file_download_link(
            str(protein_data.primary_accession))
        return protein_data
