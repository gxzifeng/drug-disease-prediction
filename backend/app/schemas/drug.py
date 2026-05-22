"""Drug Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DrugBase(BaseModel):
    """Base schema for drug."""
    id: str = Field(..., description="Drug ID (e.g., DB00001)")
    name: str = Field(..., description="Drug name")
    type: Optional[str] = Field(None, description="Drug type/category")
    description: Optional[str] = Field(None, description="Drug description")


class DrugResponse(DrugBase):
    """Schema for drug response."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    association_count: int = Field(default=0, description="Number of disease associations")
    
    class Config:
        from_attributes = True


class DrugDetailResponse(DrugResponse):
    """Schema for detailed drug response with associations."""
    known_associations: int = Field(default=0, description="Number of known associations")
    predicted_associations: int = Field(default=0, description="Number of predicted associations")


class DrugListResponse(BaseModel):
    """Schema for paginated drug list response."""
    items: List[DrugResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DrugAssociationResponse(BaseModel):
    """Schema for drug-disease association."""
    disease_id: str
    disease_name: str
    disease_category: Optional[str] = None
    association_type: str = Field(..., description="known or predicted")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class DrugAssociationsListResponse(BaseModel):
    """Schema for drug associations list."""
    drug_id: str
    drug_name: str
    associations: List[DrugAssociationResponse]
    total: int
    known_count: int
    predicted_count: int


class DrugStatisticsResponse(BaseModel):
    """Schema for drug statistics."""
    total_drugs: int
    drugs_with_associations: int
    total_associations: int
    known_associations: int
    predicted_associations: int
    type_distribution: List[dict] = Field(default_factory=list, description="Distribution by drug type")
    top_associated_drugs: List[dict] = Field(default_factory=list, description="Top drugs by association count")


class DrugFilter(BaseModel):
    """Schema for filtering drugs."""
    keyword: Optional[str] = Field(None, description="Search in name and description")
    drug_type: Optional[str] = Field(None, description="Filter by drug type")
    has_associations: Optional[bool] = Field(None, description="Filter drugs with/without associations")
