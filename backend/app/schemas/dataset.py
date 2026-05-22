"""Dataset Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============== Dataset Record Schemas ==============

class DatasetRecordBase(BaseModel):
    """Base schema for dataset record."""
    drug_id: str
    drug_name: Optional[str] = None
    disease_id: str
    disease_name: Optional[str] = None
    label: int = Field(default=1, ge=0, le=1)


class DatasetRecordCreate(DatasetRecordBase):
    """Schema for creating dataset record."""
    pass


class DatasetRecordResponse(DatasetRecordBase):
    """Schema for dataset record response."""
    id: int
    
    class Config:
        from_attributes = True


# ============== Dataset Schemas ==============

class DatasetBase(BaseModel):
    """Base schema for dataset."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    source: str = Field(default="custom", max_length=50)


class DatasetCreate(DatasetBase):
    """Schema for creating dataset (used internally)."""
    original_filename: str
    file_path: str
    file_size: int


class DatasetUpdate(BaseModel):
    """Schema for updating dataset."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    source: Optional[str] = Field(None, max_length=50)


class DatasetStats(BaseModel):
    """Dataset statistics schema."""
    drug_count: int
    disease_count: int
    association_count: int
    positive_count: int
    negative_count: int
    positive_ratio: float = Field(description="Ratio of positive samples")
    
    class Config:
        from_attributes = True


class DatasetResponse(DatasetBase):
    """Schema for dataset response."""
    id: int
    original_filename: str
    file_size: int
    drug_count: int
    disease_count: int
    association_count: int
    positive_count: int
    negative_count: int
    is_parsed: bool
    parse_error: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for paginated dataset list response."""
    items: List[DatasetResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DatasetPreviewResponse(BaseModel):
    """Schema for dataset preview response."""
    records: List[DatasetRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int
    columns: List[str] = Field(default=["drug_id", "drug_name", "disease_id", "disease_name", "label"])


# ============== Upload Request ==============

class DatasetUploadRequest(BaseModel):
    """Schema for dataset upload metadata."""
    name: str = Field(..., min_length=1, max_length=200)
    source: str = Field(default="custom", max_length=50)
    description: Optional[str] = None


# ============== Filter Schemas ==============

class DatasetFilter(BaseModel):
    """Schema for filtering datasets."""
    keyword: Optional[str] = None
    source: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
