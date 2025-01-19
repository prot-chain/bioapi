import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from starlette.status import HTTP_200_OK
from app import app

# Import your service classes
from schema.pdb import (Cell, PDBEntry,
                        Author,
                        RcsbEntryInfo,
                        Struct,
                        Symmetry,
                        RcsbEntryContainerIdentifiers,
                        RcsbAccessionInfo,
                        Cell, Citation, RevisionGroup, RevisionHistory,
                        Exptl, ExptlCrystal, RevisionCategory, RevisionDetails,
                        Diffrn
                        )
from service.pdb.fetch import PDBFetchService
from service.uniprot import UniprotFetchService

client = TestClient(app)


@pytest.fixture
def mock_uniprot_service():
    service = AsyncMock(spec=UniprotFetchService)
    return service


@pytest.fixture
def mock_pdb_service():
    service = AsyncMock(spec=PDBFetchService)
    return service


@pytest.fixture
def mock_pdb_service_3top_200():
    service = AsyncMock(spec=PDBFetchService)
    #service.fetch_protein_data.return_value = PDBEntry()
    #service.parse_protein_data.return_value = ProteinData()
    return service


@pytest.fixture
def mock_protein_endpoint_invalid_call():
    """
    mock_uniprot_service_200 mocks the uniprot service for a successful
    call
    """
    uniprot_service = AsyncMock(spec=UniprotFetchService)
    pdb_service = AsyncMock(spec=PDBFetchService)


@pytest.fixture
def override_dependencies(mock_uniprot_service, mock_pdb_service):
    app.dependency_overrides[UniprotFetchService] = lambda: mock_uniprot_service
    app.dependency_overrides[PDBFetchService] = lambda: mock_pdb_service
    yield
    app.dependency_overrides = {}


# Integration Tests
@pytest.mark.asyncio
#async def test_retrieve_protein_by_id_invalid(
#        mock_pdb_service,
#        mock_uniprot_service,
#        override_dependencies
#):
#    protein_id = "INVALID!"  # Invalid protein ID
#    response = client.get(f"/api/v1/protein/{protein_id}")
#
#    assert response.status_code == 400
#    assert response.json() == {"detail": "Invalid protein ID format."}
#    mock_pdb_service.fetch_protein_data.assert_not_called()
#    mock_uniprot_service.fetch_protein_data.assert_not_called()
#    mock_pdb_service.parse_protein_data.assert_not_called()
#    mock_uniprot_service.parse_protein_data.assert_not_called()


@pytest.mark.asyncio
async def test_retrieve_protein_by_pdb_id(
        mock_pdb_service,
        mock_uniprot_service,
        override_dependencies
):
    mock_pdb_service.fetch_protein_data.return_value = PDBEntry(
        audit_author=[
            Author(name="Fermi, G.", pdbx_ordinal=1),
            Author(name="Perutz, M.F.", pdbx_ordinal=2)
        ],
        cell=Cell(
            angle_alpha=90.0,
            angle_beta=99.34,
            angle_gamma=90.0,
            length_a=63.15,
            length_b=83.59,
            length_c=53.8,
            zpdb=4
        ),
        citation=[
            Citation(
                country="UK",
                id="primary",
                journal_abbrev="J.Mol.Biol.",
                journal_volume="175",
                page_first="159",
                page_last="174",
                title="The crystal structure of human deoxyhaemoglobin at 1.74 A resolution",
                year=1984,
                pdbx_database_id_doi="10.1016/0022-2836(84)90472-8",
                pdbx_database_id_pub_med=6726807,
                rcsb_authors=["Fermi, G.", "Perutz, M.F.", "Shaanan, B.", "Fourme, R."],
                rcsb_is_primary="Y"
            )
        ],
        diffrn=[
            Diffrn(crystal_id="1", id="1")
        ],
        exptl=[
            Exptl(method="X-RAY DIFFRACTION")
        ],
        exptl_crystal=[
            ExptlCrystal(density_matthews=2.26, density_percent_sol=45.48, id="1")
        ],
        pdbx_audit_revision_category=[
            RevisionCategory(category="atom_site", data_content_type="Structure model", ordinal=1, revision_ordinal=4)
        ],
        pdbx_audit_revision_details=[
            RevisionDetails(
                data_content_type="Structure model",
                details="Coordinates updated",
                ordinal=1,
                provider="repository",
                revision_ordinal=6,
                type="Remediation"
            )
        ],
        pdbx_audit_revision_group=[
            RevisionGroup(
                data_content_type="Structure model",
                group="Version format compliance",
                ordinal=1,
                revision_ordinal=2
            )
        ],
        pdbx_audit_revision_history=[
            RevisionHistory(
                data_content_type="Structure model",
                major_revision=4,
                minor_revision=0,
                ordinal=6,
                revision_date="2023-02-08T00:00:00+0000"
            )
        ],
        rcsb_accession_info=RcsbAccessionInfo(
            deposit_date="1984-03-07T00:00:00+0000",
            has_released_experimental_data="N",
            initial_release_date="1984-07-17T00:00:00+0000",
            major_revision=4,
            minor_revision=2,
            revision_date="2024-05-22T00:00:00+0000",
            status_code="REL"
        ),
        rcsb_entry_container_identifiers=RcsbEntryContainerIdentifiers(
            assembly_ids=["1"],
            entity_ids=["1", "2", "3", "4", "5"],
            entry_id="4HHB",
            non_polymer_entity_ids=["3", "4"],
            polymer_entity_ids=["1", "2"],
            rcsb_id="4HHB",
            pubmed_id=6726807
        ),
        rcsb_entry_info=RcsbEntryInfo(
            assembly_count=1,
            deposited_atom_count=4779,
            deposited_model_count=1,
            experimental_method="X-ray",
            molecular_weight=64.74
        ),
        struct=Struct(
            title="The crystal structure of human deoxyhaemoglobin at 1.74 A resolution"
        ),
        symmetry=Symmetry(
            int_tables_number=4,
            space_group_name_hm="P 1 21 1"
        ),
        rcsb_id="4HHB"
    )
    protein_id = "4HHB"
    response = client.get(f"/api/v1/protein/{protein_id}")
    assert response.status_code == status.HTTP_200_OK
    print(response.json())
