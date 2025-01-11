from httpx import AsyncClient


class PDBFetchService:
    """
    Service to handle fetching and parsing protein data from the PDB API.
    """

    BASE_URL = "https://data.rcsb.org/rest/v1/core/entry"

    async def fetch_protein_data(self, protein_id: str) -> dict:
        """
        Fetch raw protein data from the PDB API.

        Args:
            protein_id (str): The PDB ID of the protein.

        Returns:
            dict: Raw protein data.
        """
        async with AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/{protein_id}")
            if response.status_code != 200:
                raise Exception(f"Failed to fetch protein data for ID {protein_id}")
            return response.json()

    async def parse_protein_data(self, raw_data: dict) -> dict:
        """
        Parse raw protein data into a structured format.

        Args:
            raw_data (dict): Raw protein data.

        Returns:
            dict: Parsed protein data.
        """
        return {
            "id": raw_data.get("rcsb_id"),
            "title": raw_data.get("struct", {}).get("title"),
            "keywords": raw_data.get("struct_keywords", {}).get("text"),
            "resolution": raw_data.get("rcsb_entry_info", {}).get("resolution_combined")
        }
