from service.utils import pdb_file_download_link
from typing import Dict
from httpx import AsyncClient
from schema import (
    ProteinData, Organism, EntryAudit, DiseaseAssociation, Isoform, Feature
)


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
        res: Dict = {}
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{protein_id}?format={format}")
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch protein data for ID {protein_id}")
            res = response.json()

        async with AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{protein_id}?format=fasta")
            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch protein data for ID {protein_id}")
            res["sequence"] = response.text

        return res

    def parse_protein_data(self, data: dict) -> ProteinData:
        """
        Parse raw protein data into a structured format.

        Args:
            raw_data (dict): Raw protein data.

        Returns:
            dict: Parsed protein data.
        """

        protein_data = ProteinData(
            primary_accession=data.get("primaryAccession"),
            recommended_name=data.get("proteinDescription", {}).get(
                "recommendedName", {}).get("fullName", {}).get("value"),
            organism=Organism(
                scientific_name=data.get("organism", {}).get("scientificName"),
                common_name=data.get("organism", {}).get("commonName"),
            ),
            entry_audit=EntryAudit(
                first_public_date=data.get("entryAudit", {}).get("firstPublicDate"),
                last_annotation_update_date=data.get("entryAudit", {}).get("lastAnnotationUpdateDate"),
                sequence_version=data.get("entryAudit", {}).get("sequenceVersion"),
                entry_version=data.get("entryAudit", {}).get("entryVersion"),
            ),
            functions=[
                comment.get("texts", [{}])[0].get("value")
                for comment in data.get("comments", [])
                if comment.get("commentType") == "FUNCTION"
            ],
            subunit_structure=[
                comment.get("texts", [{}])[0].get("value")
                for comment in data.get("comments", [])
                if comment.get("commentType") == "SUBUNIT"
            ],
            subcellular_locations=[
                loc.get("location", {}).get("value")
                for comment in data.get("comments", [])
                if comment.get("commentType") == "SUBCELLULAR LOCATION"
                for loc in comment.get("subcellularLocations", [])
            ],
            disease_associations=[
                DiseaseAssociation(
                    disease_name=comment.get("disease", {}).get("description"),
                    acronym=comment.get("disease", {}).get("acronym"),
                    cross_reference=comment.get("disease", {}).get(
                        "diseaseCrossReference", {}).get("database")
                )
                for comment in data.get("comments", [])
                if comment.get("commentType") == "DISEASE"
            ],
            isoforms=[
                Isoform(
                    isoform_name=isoform.get("name", {}).get("value"),
                    sequence_status=isoform.get("isoformSequenceStatus")
                )
                for comment in data.get("comments", [])
                if comment.get("commentType") == "ALTERNATIVE PRODUCTS"
                for isoform in comment.get("isoforms", [])
            ],
            features=[
                Feature(
                    type=feature.get("type"),
                    location=f"{feature.get('location', {}).get('start', {}).get('value')} - "
                            f"{feature.get('location', {}).get('end', {}).get('value')}",
                    description=feature.get("description")
                )
                for feature in data.get("features", [])
            ],
            pdb_ids=[ref.get("id") for ref in data.get(
                        "uniProtKBCrossReferences", [])
                        if ref.get("database") == "PDB"],
            )
        protein_data.pdb_link = pdb_file_download_link(
            protein_data.pdb_ids[0]) if len(protein_data.pdb_ids) > 0 else ""
        protein_data.sequence = data.get("sequence", "")
        return protein_data
