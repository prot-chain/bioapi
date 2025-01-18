from typing import List, Optional
from pydantic import BaseModel


class EntryAudit(BaseModel):
    first_public_date: Optional[str]
    last_annotation_update_date: Optional[str]
    sequence_version: Optional[int]
    entry_version: Optional[int]


class DiseaseAssociation(BaseModel):
    disease_name: Optional[str]
    acronym: Optional[str]
    cross_reference: Optional[str]


class Isoform(BaseModel):
    isoform_name: Optional[str]
    sequence_status: Optional[str]


class Feature(BaseModel):
    type: Optional[str]
    location: Optional[str]
    description: Optional[str]


class Organism(BaseModel):
    scientific_name: Optional[str]
    common_name: Optional[str]


class ProteinData(BaseModel):
    primary_accession: Optional[str]
    recommended_name: Optional[str]
    organism: Optional[Organism]
    entry_audit: Optional[EntryAudit]
    functions: List[str]
    subunit_structure: List[str]
    subcellular_locations: List[str]
    disease_associations: List[DiseaseAssociation]
    isoforms: List[Isoform]
    features: List[Feature]
    pdb_ids: List[str]
    pdb_link: Optional[str] = None
    sequence: Optional[str] = None
