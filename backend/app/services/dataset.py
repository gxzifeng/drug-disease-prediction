"""Dataset service for business logic."""
import os
import csv
import math
import uuid
import aiofiles
from datetime import datetime
from typing import Optional, List, Tuple
from io import StringIO

from fastapi import UploadFile, HTTPException
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.dataset import Dataset, DatasetRecord
from app.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetFilter,
    DatasetStats,
    DatasetResponse,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetRecordResponse,
)


class DatasetService:
    """Service class for dataset operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_dataset(
        self,
        name: str,
        source: str,
        description: Optional[str],
        file: UploadFile,
        user_id: Optional[int] = None,
    ) -> Dataset:
        """Create a new dataset from uploaded file."""
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = file.filename.lower().split(".")[-1]
        if file_ext not in ["csv", "tsv", "txt"]:
            raise HTTPException(status_code=400, detail="Only CSV/TSV files are supported")
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_size = 0
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            file_size = len(content)
            
            # Check empty file
            if file_size == 0:
                raise HTTPException(status_code=400, detail="The uploaded file is empty")
                
            # Check file size limit
            if file_size > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
                )
                
            await f.write(content)
        
        # Create dataset record
        dataset = Dataset(
            name=name,
            description=description,
            source=source,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            created_by=user_id,
        )
        
        self.db.add(dataset)
        await self.db.flush()
        
        # Parse the file and store records
        try:
            await self._parse_and_store_records(dataset, content.decode("utf-8"), file_ext)
            dataset.is_parsed = True
        except Exception as e:
            dataset.parse_error = str(e)
            dataset.is_parsed = False
        
        await self.db.commit()
        await self.db.refresh(dataset)
        
        return dataset
    
    async def _parse_and_store_records(
        self,
        dataset: Dataset,
        content: str,
        file_ext: str
    ) -> None:
        """Parse CSV/TSV content and store records."""
        # Determine delimiter
        delimiter = "\t" if file_ext in ["tsv", "txt"] else ","
        
        # Parse CSV
        reader = csv.DictReader(StringIO(content), delimiter=delimiter)
        
        # Validate required columns
        fieldnames = reader.fieldnames or []
        fieldnames_lower = [f.lower().strip() for f in fieldnames]
        
        # Map column names (case-insensitive)
        column_map = {}
        for idx, name in enumerate(fieldnames_lower):
            if name in ["drug_id", "drugid", "drug"]:
                column_map["drug_id"] = fieldnames[idx]
            elif name in ["drug_name", "drugname"]:
                column_map["drug_name"] = fieldnames[idx]
            elif name in ["disease_id", "diseaseid", "disease"]:
                column_map["disease_id"] = fieldnames[idx]
            elif name in ["disease_name", "diseasename"]:
                column_map["disease_name"] = fieldnames[idx]
            elif name in ["label", "association", "relation"]:
                column_map["label"] = fieldnames[idx]
        
        if "drug_id" not in column_map:
            raise ValueError("Missing required column: drug_id")
        if "disease_id" not in column_map:
            raise ValueError("Missing required column: disease_id")
        
        # Track statistics
        drugs = set()
        diseases = set()
        positive_count = 0
        negative_count = 0
        records_to_add = []
        
        for row in reader:
            drug_id = row.get(column_map["drug_id"], "").strip()
            disease_id = row.get(column_map["disease_id"], "").strip()
            
            if not drug_id or not disease_id:
                continue  # Skip invalid rows
            
            drug_name = row.get(column_map.get("drug_name", ""), "").strip() or None
            disease_name = row.get(column_map.get("disease_name", ""), "").strip() or None
            
            # Parse label (default to 1 if not provided)
            label_str = row.get(column_map.get("label", ""), "1").strip()
            try:
                label = int(label_str) if label_str else 1
                label = 1 if label > 0 else 0  # Normalize to 0/1
            except ValueError:
                label = 1
            
            drugs.add(drug_id)
            diseases.add(disease_id)
            
            if label == 1:
                positive_count += 1
            else:
                negative_count += 1
            
            record = DatasetRecord(
                dataset_id=dataset.id,
                drug_id=drug_id,
                drug_name=drug_name,
                disease_id=disease_id,
                disease_name=disease_name,
                label=label,
            )
            records_to_add.append(record)
        
        if not records_to_add:
            raise ValueError("No valid records found in the file")
        
        # Batch insert records
        self.db.add_all(records_to_add)
        
        # Update dataset statistics
        dataset.drug_count = len(drugs)
        dataset.disease_count = len(diseases)
        dataset.association_count = len(records_to_add)
        dataset.positive_count = positive_count
        dataset.negative_count = negative_count
    
    async def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get dataset by ID."""
        result = await self.db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        return result.scalar_one_or_none()
    
    async def get_dataset_or_404(self, dataset_id: int) -> Dataset:
        """Get dataset by ID or raise 404."""
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset
    
    async def list_datasets(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> DatasetListResponse:
        """List datasets with filtering and pagination."""
        # Build query
        query = select(Dataset)
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    Dataset.name.ilike(f"%{keyword}%"),
                    Dataset.description.ilike(f"%{keyword}%"),
                )
            )
        
        if source:
            conditions.append(Dataset.source == source)
        
        if start_date:
            conditions.append(Dataset.created_at >= start_date)
        
        if end_date:
            conditions.append(Dataset.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(Dataset)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Dataset.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        datasets = result.scalars().all()
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return DatasetListResponse(
            items=[DatasetResponse.model_validate(d) for d in datasets],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_dataset_preview(
        self,
        dataset_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> DatasetPreviewResponse:
        """Get paginated preview of dataset records."""
        dataset = await self.get_dataset_or_404(dataset_id)
        
        # Get total count
        count_query = select(func.count()).select_from(DatasetRecord).where(
            DatasetRecord.dataset_id == dataset_id
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get records with pagination
        offset = (page - 1) * page_size
        query = (
            select(DatasetRecord)
            .where(DatasetRecord.dataset_id == dataset_id)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return DatasetPreviewResponse(
            records=[DatasetRecordResponse.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_dataset_stats(self, dataset_id: int) -> DatasetStats:
        """Get dataset statistics."""
        dataset = await self.get_dataset_or_404(dataset_id)
        
        total = dataset.positive_count + dataset.negative_count
        positive_ratio = dataset.positive_count / total if total > 0 else 0.0
        
        return DatasetStats(
            drug_count=dataset.drug_count,
            disease_count=dataset.disease_count,
            association_count=dataset.association_count,
            positive_count=dataset.positive_count,
            negative_count=dataset.negative_count,
            positive_ratio=round(positive_ratio, 4),
        )
    
    async def update_dataset(
        self,
        dataset_id: int,
        update_data: DatasetUpdate,
    ) -> Dataset:
        """Update dataset metadata."""
        dataset = await self.get_dataset_or_404(dataset_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(dataset, key, value)
        
        await self.db.commit()
        await self.db.refresh(dataset)
        
        return dataset
    
    async def delete_dataset(self, dataset_id: int) -> bool:
        """Delete dataset and associated file."""
        dataset = await self.get_dataset_or_404(dataset_id)
        
        # Delete file
        if dataset.file_path and os.path.exists(dataset.file_path):
            try:
                os.remove(dataset.file_path)
            except OSError:
                pass  # File may already be deleted
        
        # Delete from database (cascade will delete records)
        await self.db.delete(dataset)
        await self.db.commit()
        
        return True
