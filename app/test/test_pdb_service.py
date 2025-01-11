import pytest
from unittest.mock import patch
from service.pdb.fetch import PDBFetchService


@pytest.fixture
def pdb_service():
    return PDBFetchService()


@patch("service.pdb.fetch.requests.get")
def test_fetch_protein_data(mock_get, pdb_service):
    protein_id = "1HNY"
    mock_response = "PDB MOCK DATA"
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = mock_response

    _ = pdb_service.fetch_protein_data(protein_id)

    mock_get.assert_called_once_with(f"https://data.rcsb.org/rest/v1/core/entry/{protein_id}")


def test_parse_protein_data(pdb_service):
    raw_data = {"mock_key": "mock_value"}
    _ = pdb_service.parse_protein_data(raw_data)
