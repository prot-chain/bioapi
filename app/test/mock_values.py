import json
from schema.pdb import (PDBEntry,
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


mock_pdb_return = PDBEntry(
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

moc_uniprot_return = {}
with open("app/test/uniprot_test_response.json", 'r') as file:
    mock_uniprot_return = json.load(file)
