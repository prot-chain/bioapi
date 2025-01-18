from typing import List, Optional
from pydantic import BaseModel, Field


# Nested Classes
class Author(BaseModel):
    name: Optional[str] = ""
    pdbx_ordinal: Optional[int] = 0
 

class Cell(BaseModel):
    angle_alpha: Optional[float] = 0
    angle_beta: Optional[float] = 0
    angle_gamma: Optional[float] = 0
    length_a: Optional[float] = 0
    length_b: Optional[float] = 0
    length_c: Optional[float] = 0
    zpdb: Optional[int] = 0


class Citation(BaseModel):
    country: Optional[str] = ""
    id: Optional[str] = ""
    journal_abbrev: Optional[str] = ""
    journal_volume: Optional[str] = ""
    page_first: Optional[str] = ""
    page_last: Optional[str] = ""
    title: Optional[str] = ""
    year: Optional[int] = 0
    pdbx_database_id_doi: Optional[str] = ""
    pdbx_database_id_pub_med: Optional[int] = 0
    rcsb_authors: List[str] = []
    rcsb_is_primary: Optional[str] = ""


class Diffrn(BaseModel):
    crystal_id: Optional[str] = ""
    id: Optional[str] = ""


class Exptl(BaseModel):
    method: Optional[str] = ""


class ExptlCrystal(BaseModel):
    density_matthews: Optional[float] = 0
    density_percent_sol: Optional[float] = 0
    id: Optional[str] = ""


class RevisionCategory(BaseModel):
    category: Optional[str] = ""
    data_content_type: Optional[str] = ""
    ordinal: Optional[int] = 0
    revision_ordinal: Optional[int] = 0


class RevisionDetails(BaseModel):
    data_content_type: Optional[str] = ""
    details: Optional[str] = ""
    ordinal: Optional[int] = 0
    provider: Optional[str] = ""
    revision_ordinal: Optional[int] = 0
    type: Optional[str] = ""


class RevisionGroup(BaseModel):
    data_content_type: Optional[str] = ""
    group: Optional[str] = ""
    ordinal: Optional[int] = 0
    revision_ordinal: Optional[int] = 0


class RevisionHistory(BaseModel):
    data_content_type: Optional[str] = ""
    major_revision: Optional[int] = 0
    minor_revision: Optional[int] = 0
    ordinal: Optional[int] = 0
    revision_date: Optional[str] = ""


class RcsbAccessionInfo(BaseModel):
    deposit_date: Optional[str] = ""
    has_released_experimental_data: Optional[str] = ""
    initial_release_date: Optional[str] = ""
    major_revision: Optional[int] = 0
    minor_revision: Optional[int] = 0
    revision_date: Optional[str] = ""
    status_code: Optional[str] = ""


class RcsbEntryContainerIdentifiers(BaseModel):
    assembly_ids: List[str] = []
    entity_ids: List[str] = []
    entry_id: Optional[str] = ""
    m_identifiers: List[int] = Field(alias="model_ids")
    non_polymer_entity_ids: List[str] = []
    polymer_entity_ids: List[str] = []
    rcsb_id: Optional[str] = ""
    pubmed_id: Optional[int] = 0


class RcsbEntryInfo(BaseModel):
    assembly_count: Optional[int] = 0
    deposited_atom_count: Optional[int] = 0
    deposited_model_count: Optional[int] = 0
    experimental_method: Optional[str] = ""
    molecular_weight: Optional[float] = 0


class Struct(BaseModel):
    title: Optional[str] = ""


class Symmetry(BaseModel):
    int_tables_number: Optional[int] = 0
    space_group_name_hm: Optional[str] = ""


# Main Class
class PDBEntry(BaseModel):
    audit_author: List[Author] = []
    cell: Optional[Cell] = Cell()
    citation: List[Citation] = []
    diffrn: List[Diffrn] = []
    exptl: List[Exptl] = []
    exptl_crystal: List[ExptlCrystal] = []
    pdbx_audit_revision_category: List[RevisionCategory] = []
    pdbx_audit_revision_details: List[RevisionDetails] = []
    pdbx_audit_revision_group: List[RevisionGroup] = []
    pdbx_audit_revision_history: List[RevisionHistory] = []
    rcsb_accession_info: Optional[RcsbAccessionInfo] = RcsbAccessionInfo()
    rcsb_entry_container_identifiers: Optional[RcsbEntryContainerIdentifiers]
    rcsb_entry_info: Optional[RcsbEntryInfo] = RcsbEntryInfo()
    struct: Optional[Struct] = Struct()
    symmetry: Optional[Symmetry] = Symmetry()
    rcsb_id: Optional[str] = ""
