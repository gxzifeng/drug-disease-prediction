"""Disease service for business logic operations."""
import math
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.schemas.disease import (
    DiseaseResponse,
    DiseaseDetailResponse,
    DiseaseListResponse,
    DiseaseAssociationResponse,
    DiseaseAssociationsListResponse,
    DiseaseStatisticsResponse,
)


class DiseaseService:
    """Service class for disease-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_diseases(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        has_associations: Optional[bool] = None,
    ) -> DiseaseListResponse:
        """
        List diseases with filtering and pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            keyword: Search keyword for name/description
            category: Filter by disease category
            has_associations: Filter by whether disease has associations
        
        Returns:
            Paginated list of diseases
        """
        # Build base query with association count
        base_query = """
            SELECT 
                ds.id,
                ds.name,
                ds.category,
                ds.description,
                ds.created_at,
                ds.updated_at,
                COUNT(dda.id) as association_count
            FROM diseases ds
            LEFT JOIN drug_disease_associations dda ON ds.id = dda.disease_id
        """
        
        conditions = []
        params = {}
        
        if keyword:
            conditions.append("(ds.name LIKE :keyword OR ds.description LIKE :keyword)")
            params["keyword"] = f"%{keyword}%"
        
        if category:
            conditions.append("ds.category = :category")
            params["category"] = category
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Group by and having clause for association filter
        group_clause = "GROUP BY ds.id, ds.name, ds.category, ds.description, ds.created_at, ds.updated_at"
        
        having_clause = ""
        if has_associations is not None:
            if has_associations:
                having_clause = "HAVING COUNT(dda.id) > 0"
            else:
                having_clause = "HAVING COUNT(dda.id) = 0"
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM (
                SELECT ds.id
                FROM diseases ds
                LEFT JOIN drug_disease_associations dda ON ds.id = dda.disease_id
                {where_clause}
                {group_clause}
                {having_clause}
            ) as subq
        """
        
        count_result = await self.db.execute(text(count_query), params)
        total = count_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        
        data_query = f"""
            {base_query}
            {where_clause}
            {group_clause}
            {having_clause}
            ORDER BY ds.name ASC
            LIMIT :limit OFFSET :offset
        """
        
        result = await self.db.execute(text(data_query), params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            items.append(DiseaseResponse(
                id=row.id,
                name=row.name,
                category=row.category,
                description=row.description,
                created_at=row.created_at,
                updated_at=row.updated_at,
                association_count=row.association_count or 0,
            ))
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return DiseaseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_disease(self, disease_id: str) -> Optional[DiseaseDetailResponse]:
        """
        Get disease by ID with detailed information.
        
        Args:
            disease_id: Disease identifier
        
        Returns:
            Disease details or None if not found
        """
        query = """
            SELECT 
                ds.id,
                ds.name,
                ds.category,
                ds.description,
                ds.created_at,
                ds.updated_at,
                COUNT(dda.id) as association_count,
                SUM(CASE WHEN dda.association_type = 'known' THEN 1 ELSE 0 END) as known_associations,
                SUM(CASE WHEN dda.association_type = 'predicted' THEN 1 ELSE 0 END) as predicted_associations
            FROM diseases ds
            LEFT JOIN drug_disease_associations dda ON ds.id = dda.disease_id
            WHERE ds.id = :disease_id
            GROUP BY ds.id, ds.name, ds.category, ds.description, ds.created_at, ds.updated_at
        """
        
        result = await self.db.execute(text(query), {"disease_id": disease_id})
        row = result.fetchone()
        
        if not row or not row.id:
            return None
        
        return DiseaseDetailResponse(
            id=row.id,
            name=row.name,
            category=row.category,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            association_count=row.association_count or 0,
            known_associations=row.known_associations or 0,
            predicted_associations=row.predicted_associations or 0,
        )
    
    async def get_disease_or_404(self, disease_id: str) -> DiseaseDetailResponse:
        """Get disease by ID or raise 404 error."""
        disease = await self.get_disease(disease_id)
        if not disease:
            raise HTTPException(status_code=404, detail=f"Disease {disease_id} not found")
        return disease
    
    async def get_disease_associations(
        self,
        disease_id: str,
        association_type: Optional[str] = None,
        limit: int = 50,
    ) -> DiseaseAssociationsListResponse:
        """
        Get all drug associations for a disease.
        
        Args:
            disease_id: Disease identifier
            association_type: Filter by 'known' or 'predicted'
            limit: Maximum number of associations to return
        
        Returns:
            List of drug associations
        """
        # First verify disease exists
        disease = await self.get_disease_or_404(disease_id)
        
        # Build query for associations
        query = """
            SELECT 
                dda.drug_id,
                d.name as drug_name,
                d.type as drug_type,
                dda.association_type,
                dda.confidence_score
            FROM drug_disease_associations dda
            JOIN drugs d ON dda.drug_id = d.id
            WHERE dda.disease_id = :disease_id
        """
        
        params = {"disease_id": disease_id, "limit": limit}
        
        if association_type:
            query += " AND dda.association_type = :association_type"
            params["association_type"] = association_type
        
        query += " ORDER BY dda.confidence_score DESC NULLS LAST, d.name ASC LIMIT :limit"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        associations = []
        known_count = 0
        predicted_count = 0
        
        for row in rows:
            associations.append(DiseaseAssociationResponse(
                drug_id=row.drug_id,
                drug_name=row.drug_name,
                drug_type=row.drug_type,
                association_type=row.association_type,
                confidence_score=row.confidence_score,
            ))
            if row.association_type == 'known':
                known_count += 1
            else:
                predicted_count += 1
        
        return DiseaseAssociationsListResponse(
            disease_id=disease.id,
            disease_name=disease.name,
            associations=associations,
            total=len(associations),
            known_count=known_count,
            predicted_count=predicted_count,
        )
    
    async def get_disease_statistics(self) -> DiseaseStatisticsResponse:
        """
        Get overall disease statistics.
        
        Returns:
            Statistics about diseases and their associations
        """
        # Total diseases
        total_query = "SELECT COUNT(*) FROM diseases"
        total_result = await self.db.execute(text(total_query))
        total_diseases = total_result.scalar() or 0
        
        # Diseases with associations
        with_assoc_query = """
            SELECT COUNT(DISTINCT disease_id) 
            FROM drug_disease_associations
        """
        with_assoc_result = await self.db.execute(text(with_assoc_query))
        diseases_with_associations = with_assoc_result.scalar() or 0
        
        # Association counts
        assoc_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN association_type = 'known' THEN 1 ELSE 0 END) as known,
                SUM(CASE WHEN association_type = 'predicted' THEN 1 ELSE 0 END) as predicted
            FROM drug_disease_associations
        """
        assoc_result = await self.db.execute(text(assoc_query))
        assoc_row = assoc_result.fetchone()
        
        # Category distribution
        category_query = """
            SELECT category, COUNT(*) as count
            FROM diseases
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """
        category_result = await self.db.execute(text(category_query))
        category_distribution = [
            {"category": row.category, "count": row.count}
            for row in category_result.fetchall()
        ]
        
        # Top associated diseases
        top_query = """
            SELECT ds.id, ds.name, ds.category, COUNT(dda.id) as association_count
            FROM diseases ds
            JOIN drug_disease_associations dda ON ds.id = dda.disease_id
            GROUP BY ds.id, ds.name, ds.category
            ORDER BY association_count DESC
            LIMIT 10
        """
        top_result = await self.db.execute(text(top_query))
        top_associated_diseases = [
            {
                "id": row.id,
                "name": row.name,
                "category": row.category,
                "association_count": row.association_count
            }
            for row in top_result.fetchall()
        ]
        
        return DiseaseStatisticsResponse(
            total_diseases=total_diseases,
            diseases_with_associations=diseases_with_associations,
            total_associations=assoc_row.total or 0 if assoc_row else 0,
            known_associations=assoc_row.known or 0 if assoc_row else 0,
            predicted_associations=assoc_row.predicted or 0 if assoc_row else 0,
            category_distribution=category_distribution,
            top_associated_diseases=top_associated_diseases,
        )
    
    async def get_disease_categories(self) -> List[str]:
        """Get list of all disease categories."""
        query = """
            SELECT DISTINCT category 
            FROM diseases 
            WHERE category IS NOT NULL 
            ORDER BY category
        """
        result = await self.db.execute(text(query))
        return [row.category for row in result.fetchall()]
