import logging

from fastapi import APIRouter, Depends, HTTPException

from service.uniprot import UniprotFetchService

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/protein/{protein_id}", summary="Retrieve Protein From PDB")
async def retrieve_protein_from_pdb(
        protein_id: str,
        uniprot_fetch_service: UniprotFetchService = Depends()
):
    """
    Fetch protein data from the PDB API using the given protein ID.

    Args:
        protein_id (str): The PDB ID of the protein.

    Returns:
        dict: Protein structure and parsed data.
    """
    # Validate protein_id format before making an API call
    if not protein_id.isalnum() or len(protein_id) != 4:
        raise HTTPException(
            status_code=400,
            detail="Invalid protein ID format. "
                   "Expected a 4-character alphanumeric ID."
        )

    try:
        raw_data = uniprot_fetch_service.fetch_protein_data(protein_id)

        # Extracting protein structure
        protein_structure = raw_data.get("structure")
        if not protein_structure:
            raise Exception("Protein structure data is missing.")

        parsed_data = uniprot_fetch_service.parse_protein_data(raw_data)
        return {
            "protein_id": protein_id,
            "structure": protein_structure,
            "data": parsed_data
        }

    except Exception as e:
        logger.error(f"Error fetching data for protein ID {protein_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
