"""Disease Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DiseaseBase(BaseModel):
    """Base schema for disease."""
    id: str = Field(..., description="Disease ID (e.g., DOID:1612)")
    name: str = Field(..., description="Disease name")
    category: Optional[str] = Field(None, description="Disease category")
    description: Optional[str] = Field(None, description="Disease description")


class DiseaseResponse(DiseaseBase):
    """Schema for disease response."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    association_count: int = Field(default=0, description="Number of drug associations")
    
    class Config:
        from_attributes = True


class DiseaseDetailResponse(DiseaseResponse):
    """Schema for detailed disease response with associations."""
    known_associations: int = Field(default=0, description="Number of known associations")
    predicted_associations: int = Field(default=0, description="Number of predicted associations")


class DiseaseListResponse(BaseModel):
    """Schema for paginated disease list response."""
    items: List[DiseaseResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DiseaseAssociationResponse(BaseModel):
    """Schema for disease-drug association."""
    drug_id: str
    drug_name: str
    drug_type: Optional[str] = None
    association_type: str = Field(..., description="known or predicted")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class DiseaseAssociationsListResponse(BaseModel):
    """Schema for disease associations list."""
    disease_id: str
    disease_name: str
    associations: List[DiseaseAssociationResponse]
    total: int
    known_count: int
    predicted_count: int


class DiseaseStatisticsResponse(BaseModel):
    """Schema for disease statistics."""
    total_diseases: int
    diseases_with_associations: int
    total_associations: int
    known_associations: int
    predicted_associations: int
    category_distribution: List[dict] = Field(default_factory=list, description="Distribution by disease category")
    top_associated_diseases: List[dict] = Field(default_factory=list, description="Top diseases by association count")


class DiseaseFilter(BaseModel):
    """Schema for filtering diseases."""
    keyword: Optional[str] = Field(None, description="Search in name and description")
    category: Optional[str] = Field(None, description="Filter by disease category")
    has_associations: Optional[bool] = Field(None, description="Filter diseases with/without associations")
