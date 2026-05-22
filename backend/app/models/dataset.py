"""Dataset database model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dataset(Base):
    """Dataset model for storing drug-disease association data."""
    
    __tablename__ = "datasets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="custom", index=True)
    
    # File information
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    
    # Statistics (computed after parsing)
    drug_count: Mapped[int] = mapped_column(Integer, default=0)
    disease_count: Mapped[int] = mapped_column(Integer, default=0)
    association_count: Mapped[int] = mapped_column(Integer, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)  # label=1
    negative_count: Mapped[int] = mapped_column(Integer, default=0)  # label=0
    
    # Status
    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    records: Mapped[list["DatasetRecord"]] = relationship(
        "DatasetRecord", back_populates="dataset", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Dataset {self.name} (id={self.id})>"


class DatasetRecord(Base):
    """Individual drug-disease association record."""
    
    __tablename__ = "dataset_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core fields (matching plan schema)
    drug_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    drug_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    disease_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    disease_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    label: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 0/1 association
    
    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="records")
    
    def __repr__(self) -> str:
        return f"<DatasetRecord drug={self.drug_id} disease={self.disease_id} label={self.label}>"
