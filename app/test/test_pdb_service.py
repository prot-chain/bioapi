import pytest
from service.pdb.fetch import PDBFetchService
from schema.pdb import PDBEntry
from schema.protein import ProteinData, EntryAudit
from service.utils import pdb_file_download_link

# Sample mock data for PDBEntry
mock_pdb_entry = PDBEntry(
    rcsb_entry_container_identifiers={"entry_id": "4HHB"},
    rcsb_accession_info={
        "initial_release_date": "1984-07-17",
        "revision_date": "2024-05-22",
        "major_revision": 4,
        "minor_revision": 2
    }
)

# Expected output for ProteinData
expected_protein_data = ProteinData(
    primary_accession="4HHB",
    entry_audit=EntryAudit(
        first_public_date="1984-07-17",
        last_annotation_update_date="2024-05-22",
        sequence_version=4,
        entry_version=2,
    ),
    pdb_link="https://example.com/pdb/4HHB"
)


@pytest.fixture
def pdb_service():
    """Fixture to provide an instance of PDBFetchService."""
    return PDBFetchService()


@pytest.mark.asyncio
async def test_fetch_protein_data(pdb_service, httpx_mock):
    """Test fetch_protein_data method using pytest-httpx."""
    protein_id = "4HHB"
    mock_url = f"https://data.rcsb.org/rest/v1/core/entry/{protein_id}"

    # Register mock response
    httpx_mock.add_response(
        url=mock_url,
        json=mock_pdb_entry.model_dump(),
        status_code=200
    )

    # Call the method
    fetched_data = await pdb_service.fetch_protein_data(protein_id)

    # Assertions
    assert fetched_data.rcsb_entry_container_identifiers.entry_id == "4HHB"
    assert httpx_mock.get_request()


@pytest.mark.asyncio
async def test_parse_protein_data(pdb_service):
    """Test parse_protein_data method."""
    # Call the method
    parsed_data = await pdb_service.parse_protein_data(mock_pdb_entry)

    # Assertions
    assert parsed_data.primary_accession == expected_protein_data.primary_accession
    assert parsed_data.entry_audit.first_public_date == expected_protein_data.entry_audit.first_public_date
    assert parsed_data.pdb_link == pdb_file_download_link("4HHB")
