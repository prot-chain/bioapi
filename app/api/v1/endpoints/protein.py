import logging
from fastapi import APIRouter, Depends, HTTPException
from service.pdb.fetch import PDBFetchService
from service.uniprot import UniprotFetchService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{protein_id}", summary="Retrieve Protein With ID")
async def retrieve_protein_by_id(
    protein_id: str,
    pdb_fetch_service: PDBFetchService = Depends(),
    uniprot_fetch_service: UniprotFetchService = Depends()
):
    """
    Fetch protein data from the PDB or UNIPROT API using the given protein ID.

    Args:
        protein_id (str): The PDB ID of the protein.

    Returns:
        dict: Protein structure and parsed data.
    """

    if not protein_id.isalnum():
        raise HTTPException(
            status_code=400,
            detail="Invalid protein ID format."
        )

    match len(protein_id):
        case 6:
            try:
                raw_data = await uniprot_fetch_service.fetch_protein_data(protein_id)

                # Extracting protein structure; Figure this part out with uniprot

                parsed_data = uniprot_fetch_service.parse_protein_data(raw_data)
                return {
                    "protein_id": protein_id,
                    "data": parsed_data
                }

            except Exception as e:
                logger.error(f"Error fetching data for protein ID {protein_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        case 4:

            try:
                raw_data = await pdb_fetch_service.fetch_protein_data(protein_id)

                # Extracting protein structure
                parsed_data = await pdb_fetch_service.parse_protein_data(raw_data)
                return {
                    "protein_id": protein_id,
                    "data": parsed_data
                }

            except Exception as e:
                logger.error(f"Error fetching data for protein ID {protein_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
