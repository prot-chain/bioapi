import logging
from fastapi import APIRouter, Depends, HTTPException
from httpx import AsyncClient
from app.service.pdb.fetch import PDBFetchService
from app.service.uniprot import UniprotFetchService
from app.service.storage.ipfs import store_on_ipfs, calculate_hash

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
                try:
                    # Fetch metadata
                    raw_data = await pdb_fetch_service.fetch_protein_data(protein_id)
                    parsed_data = await pdb_fetch_service.parse_protein_data(raw_data)
                    
                    # Get PDB file content
                    async with AsyncClient() as client:
                        logger.info(f"Fetching PDB file from: {parsed_data.pdb_link}")
                        pdb_response = await client.get(parsed_data.pdb_link)
                        if pdb_response.status_code != 200:
                            raise HTTPException(
                                status_code=404,
                                detail=f"PDB file not found for ID {protein_id}"
                            )
                        
                        # Store PDB file on IPFS
                        pdb_content = pdb_response.text
                        ipfs_cid = await store_on_ipfs(pdb_content)
                        
                        # Calculate file hash
                        file_hash = calculate_hash(pdb_content)
                        
                        # Return metadata, file content, and blockchain info
                        return {
                            "protein_id": protein_id,
                            "data": parsed_data.dict(),
                            "file": pdb_content,
                            "blockchain_info": {
                                "ipfs_cid": ipfs_cid,
                                "file_hash": file_hash
                            }
                        }
                except Exception as e:
                    logger.error(f"Error processing protein {protein_id}: {str(e)}")
                    raise HTTPException(status_code=404, detail=str(e))

            except Exception as e:
                logger.error(f"Error fetching data for protein ID {protein_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
