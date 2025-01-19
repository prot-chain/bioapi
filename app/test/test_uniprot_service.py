import pytest
from pytest_httpx import HTTPXMock
from service.uniprot.fetch import UniprotFetchService
from schema import ProteinData, EntryAudit, Organism

# Mock FASTA sequence
mock_fasta_sequence = ">Mock FASTA Header\nMTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVE\n"

# Mock JSON response from UniProt API
mock_uniprot_response = {
    "primaryAccession": "P12345",
    "proteinDescription": {
        "recommendedName": {"fullName": {"value": "Mock Protein"}}
    },
    "organism": {
        "scientificName": "Homo sapiens",
        "commonName": "Human"
    },
    "entryAudit": {
        "firstPublicDate": "2000-01-01",
        "lastAnnotationUpdateDate": "2023-01-01",
        "sequenceVersion": 1,
        "entryVersion": 42
    },
    "comments": [],
    "features": [],
    "uniProtKBCrossReferences": [
        {"database": "PDB", "id": "4HHB"}
    ],
    "sequence": mock_fasta_sequence
}


# Expected ProteinData output
expected_protein_data = ProteinData(
    primary_accession="P12345",
    recommended_name="Mock Protein",
    organism=Organism(
        scientific_name="Homo sapiens",
        common_name="Human"
    ),
    entry_audit=EntryAudit(
        first_public_date="2000-01-01",
        last_annotation_update_date="2023-01-01",
        sequence_version=1,
        entry_version=42
    ),
    functions=[],
    subunit_structure=[],
    subcellular_locations=[],
    disease_associations=[],
    isoforms=[],
    features=[],
    pdb_ids=["4HHB"],
    pdb_link="https://files.rcsb.org/download/4HHB.pdb.gz",
    sequence=mock_fasta_sequence
)

@pytest.fixture
def uniprot_service():
    """Fixture to provide an instance of UniprotFetchService."""
    return UniprotFetchService()


@pytest.mark.asyncio
async def test_fetch_protein_data(uniprot_service, httpx_mock: HTTPXMock):
    """Test fetch_protein_data method using pytest-httpx."""
    protein_id = "P12345"

    # Register mock responses
    httpx_mock.add_response(
        url=f"https://rest.uniprot.org/uniprotkb/{protein_id}?format=json",
        json=mock_uniprot_response,
        status_code=200
    )
    httpx_mock.add_response(
        url=f"https://rest.uniprot.org/uniprotkb/{protein_id}?format=fasta",
        text=mock_fasta_sequence,
        status_code=200
    )

    # Call the method
    result = await uniprot_service.fetch_protein_data(protein_id)
    __import__('pprint').pprint(result)

    # Assertions
    assert result["primaryAccession"] == mock_uniprot_response["primaryAccession"]
    assert result["sequence"] == mock_fasta_sequence
    assert len(httpx_mock.get_requests()) == 2


def test_parse_protein_data(uniprot_service):
    """Test parse_protein_data method."""
    # Call the method
    parsed_data = uniprot_service.parse_protein_data(mock_uniprot_response)
    __import__('pprint').pprint(parsed_data)

    # Assertions
    assert parsed_data.primary_accession == expected_protein_data.primary_accession
    assert parsed_data.recommended_name == expected_protein_data.recommended_name
    assert parsed_data.entry_audit.first_public_date == expected_protein_data.entry_audit.first_public_date
    assert parsed_data.sequence == expected_protein_data.sequence
    assert parsed_data.pdb_link == expected_protein_data.pdb_link 
