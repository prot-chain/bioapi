from unittest.mock import patch
import pytest
from service.uniprot import UniprotFetchService


@pytest.fixture
def uniprot_service():
    return UniprotFetchService()


@patch("service.uniprot.fetch.requests.get")
def test_fetch_protein_data(mock_get, uniprot_service):
    protein_id = "P12345"
    mock_response = {"name": "Mock Protein"}
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    _ = uniprot_service.fetch_protein_data(protein_id)

    mock_get.assert_called_once_with(f"https://www.uniprot.org/uniprotkb/{protein_id}.json")


def test_parse_protein_data(uniprot_service):
    raw_data = {"name": "Mock Protein"}
    result = uniprot_service.parse_protein_data(raw_data)
