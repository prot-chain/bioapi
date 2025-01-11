from httpx import AsyncClient


class UniprotFetchService:
    """
    Service to handle fetching and parsing protein data from the PDB API.
    """

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    async def fetch_protein_data(self, protein_id: str) -> dict:
        """
        Fetch raw protein data from the PDB API.

        Args:
            protein_id (str): The PDB ID of the protein.

        Returns:
            dict: Raw protein data.
        """
        async with AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/{protein_id}?format=json")
            if response.status_code != 200:
                raise Exception(f"Failed to fetch protein data for ID {protein_id}")
            return response.json()

    def parse_protein_data(self, raw_data: dict) -> dict:
        """
        Parse raw protein data into a structured format.

        Args:
            raw_data (dict): Raw protein data.

        Returns:
            dict: Parsed protein data.
        """
        return {
            "id": raw_data.get("primaryAccession"),
            "name": raw_data.get("protein", {}).get("recommendedName", {}).get("fullName", {}).get("value"),
            "organism": raw_data.get("organism", {}).get("scientificName"),
            "sequence": raw_data.get("sequence", {}).get("value"),
            "length": raw_data.get("sequence", {}).get("length"),
        }
