from httpx import AsyncClient


class UniprotFetchService:
    """
    Service to handle fetching and parsing protein data from the PDB API.
    """

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    async def fetch_protein_data(self, protein_id: str, format: str="json") -> dict:
        """
        Fetch raw protein data from the PDB API.

        Args:
            protein_id (str): The PDB ID of the protein.

        Returns:
            dict: Raw protein data.
        """
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{protein_id}?format={format}")
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch protein data for ID {protein_id}")
            print(response.json()) 
            return response.json()

    def parse_protein_data(self, data: dict) -> dict:
        """
        Parse raw protein data into a structured format.

        Args:
            raw_data (dict): Raw protein data.

        Returns:
            dict: Parsed protein data.
        """

        parsed_data = {
            "primary_accesion": data.get("primaryAccession"),
            "recommended_name": data.get("proteinDescription", {}).get(
                "recommendedName", {}).get("fullName", {}).get("value"),
            "organism": {
                "scientific_name": data.get("organism", {}).get(
                    "scientificName"),
                "common_name": data.get("organism", {}).get("commonName"),
            },
            "entry_audit": {
                "First Public Date": data.get("entryAudit", {}).get(
                    "firstPublicDate"),
                "Last Annotation Update Date": data.get("entryAudit", {}).get(
                    "lastAnnotationUpdateDate"),
                "Sequence Version": data.get("entryAudit", {}).get(
                    "sequenceVersion"),
                "Entry Version": data.get("entryAudit", {}).get(
                    "entryVersion"),
            },
            "functions": [
                comment.get("texts", [{}])[0].get("value")
                for comment in data.get("comments", [])
                if comment.get("commentType") == "FUNCTION"
            ],
            "subunit_structure": [
                comment.get("texts", [{}])[0].get("value")
                for comment in data.get("comments", [])
                if comment.get("commentType") == "SUBUNIT"
            ],
            "subcellular_locations": [
                loc.get("location", {}).get("value")
                for comment in data.get("comments", [])
                if comment.get("commentType") == "SUBCELLULAR LOCATION"
                for loc in comment.get("subcellularLocations", [])
            ],
            "Disease Associations": [
                {
                    "Disease Name": comment.get("disease", {}).get("description"),
                    "Acronym": comment.get("disease", {}).get("acronym"),
                    "Cross Reference": comment.get("disease", {}).get(
                        "diseaseCrossReference", {}).get("database")
                }
                for comment in data.get("comments", [])
                if comment.get("commentType") == "DISEASE"
            ],
            "isoforms": [
                {
                    "Isoform Name": isoform.get("name", {}).get("value"),
                    "Sequence Status": isoform.get("isoformSequenceStatus")
                }
                for comment in data.get("comments", [])
                if comment.get("commentType") == "ALTERNATIVE PRODUCTS"
                for isoform in comment.get("isoforms", [])
            ],
            "features": [
                {
                    "Type": feature.get("type"),
                    "Location": f"{feature.get('location', {}).get('start', {}).get(
                                'value')} - {feature.get('location', {}).get(
                                    'end', {}).get('value')}",
                    "Description": feature.get("description")
                }
                for feature in data.get("features", [])
            ],
        }

        return parsed_data
