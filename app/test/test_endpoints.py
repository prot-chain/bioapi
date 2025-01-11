import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app import app  # Replace with your actual FastAPI app

# Import your service classes
from service.pdb.fetch import PDBFetchService
from service.uniprot import UniprotFetchService

client = TestClient(app)


# Mock Dependencies
@pytest.fixture
def mock_uniprot_service():
    service = AsyncMock(spec=UniprotFetchService)
    service.fetch_protein_data.return_value = {"mock_key": "mock_value"}
    service.parse_protein_data.return_value = {"parsed_key": "parsed_value"}
    return service


@pytest.fixture
def mock_pdb_service():
    service = AsyncMock(spec=PDBFetchService)
    service.fetch_protein_data.return_value = {"mock_key": "mock_value"}
    service.parse_protein_data.return_value = {"parsed_key": "parsed_value"}
    return service


@pytest.fixture
def override_dependencies(mock_uniprot_service, mock_pdb_service):
    app.dependency_overrides[UniprotFetchService] = lambda: mock_uniprot_service
    app.dependency_overrides[PDBFetchService] = lambda: mock_pdb_service
    yield
    app.dependency_overrides = {}


# Integration Tests
@pytest.mark.asyncio
async def test_retrieve_protein_by_id_uniprot(mock_uniprot_service, override_dependencies):
    protein_id = "P12345"  # Example UniProt ID (6 characters)
    response = client.get(f"/api/v1/protein/{protein_id}")

    assert response.status_code == 200
    assert response.json() == {
        "protein_id": protein_id,
        "data": {"parsed_key": "parsed_value"}
    }

    # Ensure the mock service methods were called
    mock_uniprot_service.fetch_protein_data.assert_called_once_with(protein_id)
    mock_uniprot_service.parse_protein_data.assert_called_once_with(
        {"mock_key": "mock_value"}
    )


@pytest.mark.asyncio
async def test_retrieve_protein_by_id_pdb(mock_pdb_service, override_dependencies):
    protein_id = "1HNY"  # Example PDB ID (4 characters)
    response = client.get(f"/api/v1/protein/{protein_id}")

    assert response.status_code == 200
    assert response.json() == {
        "protein_id": protein_id,
        "data": {"parsed_key": "parsed_value"}
    }

    # Ensure the mock service methods were called
    mock_pdb_service.fetch_protein_data.assert_called_once_with(protein_id)
    mock_pdb_service.parse_protein_data.assert_called_once_with(
        {"mock_key": "mock_value"}
    )


@pytest.mark.asyncio
async def test_retrieve_protein_by_id_invalid():
    protein_id = "INVALID!"  # Invalid protein ID
    response = client.get(f"/api/v1/protein/{protein_id}")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid protein ID format."}


@pytest.mark.asyncio
async def test_retrieve_protein_by_id_uniprot_service_failure(mock_uniprot_service, override_dependencies):
    mock_uniprot_service.fetch_protein_data.side_effect = Exception("UniProt API Error")

    protein_id = "P12345"  # Example UniProt ID
    response = client.get(f"/api/v1/protein/{protein_id}")

    assert response.status_code == 500
    assert "UniProt API Error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_retrieve_protein_by_id_pdb_service_failure(mock_pdb_service, override_dependencies):
    mock_pdb_service.fetch_protein_data.side_effect = Exception("PDB API Error")

    protein_id = "1HNY"  # Example PDB ID
    response = client.get(f"/api/v1/protein/{protein_id}")

    assert response.status_code == 500
    assert "PDB API Error" in response.json()["detail"]

