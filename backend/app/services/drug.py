"""Drug service for business logic operations."""
import math
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.schemas.drug import (
    DrugResponse,
    DrugDetailResponse,
    DrugListResponse,
    DrugAssociationResponse,
    DrugAssociationsListResponse,
    DrugStatisticsResponse,
)


class DrugService:
    """Service class for drug-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_drugs(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: Optional[str] = None,
        drug_type: Optional[str] = None,
        has_associations: Optional[bool] = None,
    ) -> DrugListResponse:
        """
        List drugs with filtering and pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            keyword: Search keyword for name/description
            drug_type: Filter by drug type
            has_associations: Filter by whether drug has associations
        
        Returns:
            Paginated list of drugs
        """
        # Build base query with association count
        base_query = """
            SELECT 
                d.id,
                d.name,
                d.type,
                d.description,
                d.created_at,
                d.updated_at,
                COUNT(dda.id) as association_count
            FROM drugs d
            LEFT JOIN drug_disease_associations dda ON d.id = dda.drug_id
        """
        
        conditions = []
        params = {}
        
        if keyword:
            conditions.append("(d.name LIKE :keyword OR d.description LIKE :keyword)")
            params["keyword"] = f"%{keyword}%"
        
        if drug_type:
            conditions.append("d.type = :drug_type")
            params["drug_type"] = drug_type
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Group by and having clause for association filter
        group_clause = "GROUP BY d.id, d.name, d.type, d.description, d.created_at, d.updated_at"
        
        having_clause = ""
        if has_associations is not None:
            if has_associations:
                having_clause = "HAVING COUNT(dda.id) > 0"
            else:
                having_clause = "HAVING COUNT(dda.id) = 0"
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM (
                SELECT d.id
                FROM drugs d
                LEFT JOIN drug_disease_associations dda ON d.id = dda.drug_id
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
            ORDER BY d.name ASC
            LIMIT :limit OFFSET :offset
        """
        
        result = await self.db.execute(text(data_query), params)
        rows = result.fetchall()
        
        items = []
        for row in rows:
            items.append(DrugResponse(
                id=row.id,
                name=row.name,
                type=row.type,
                description=row.description,
                created_at=row.created_at,
                updated_at=row.updated_at,
                association_count=row.association_count or 0,
            ))
        
        pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return DrugListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    
    async def get_drug(self, drug_id: str) -> Optional[DrugDetailResponse]:
        """
        Get drug by ID with detailed information.
        
        Args:
            drug_id: Drug identifier
        
        Returns:
            Drug details or None if not found
        """
        query = """
            SELECT 
                d.id,
                d.name,
                d.type,
                d.description,
                d.created_at,
                d.updated_at,
                COUNT(dda.id) as association_count,
                SUM(CASE WHEN dda.association_type = 'known' THEN 1 ELSE 0 END) as known_associations,
                SUM(CASE WHEN dda.association_type = 'predicted' THEN 1 ELSE 0 END) as predicted_associations
            FROM drugs d
            LEFT JOIN drug_disease_associations dda ON d.id = dda.drug_id
            WHERE d.id = :drug_id
            GROUP BY d.id, d.name, d.type, d.description, d.created_at, d.updated_at
        """
        
        result = await self.db.execute(text(query), {"drug_id": drug_id})
        row = result.fetchone()
        
        if not row or not row.id:
            return None
        
        return DrugDetailResponse(
            id=row.id,
            name=row.name,
            type=row.type,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            association_count=row.association_count or 0,
            known_associations=row.known_associations or 0,
            predicted_associations=row.predicted_associations or 0,
        )
    
    async def get_drug_or_404(self, drug_id: str) -> DrugDetailResponse:
        """Get drug by ID or raise 404 error."""
        drug = await self.get_drug(drug_id)
        if not drug:
            raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")
        return drug
    
    async def get_drug_associations(
        self,
        drug_id: str,
        association_type: Optional[str] = None,
        limit: int = 50,
    ) -> DrugAssociationsListResponse:
        """
        Get all disease associations for a drug.
        
        Args:
            drug_id: Drug identifier
            association_type: Filter by 'known' or 'predicted'
            limit: Maximum number of associations to return
        
        Returns:
            List of disease associations
        """
        # First verify drug exists
        drug = await self.get_drug_or_404(drug_id)
        
        # Build query for associations
        query = """
            SELECT 
                dda.disease_id,
                ds.name as disease_name,
                ds.category as disease_category,
                dda.association_type,
                dda.confidence_score
            FROM drug_disease_associations dda
            JOIN diseases ds ON dda.disease_id = ds.id
            WHERE dda.drug_id = :drug_id
        """
        
        params = {"drug_id": drug_id, "limit": limit}
        
        if association_type:
            query += " AND dda.association_type = :association_type"
            params["association_type"] = association_type
        
        query += " ORDER BY dda.confidence_score DESC NULLS LAST, ds.name ASC LIMIT :limit"
        
        result = await self.db.execute(text(query), params)
        rows = result.fetchall()
        
        associations = []
        known_count = 0
        predicted_count = 0
        
        for row in rows:
            associations.append(DrugAssociationResponse(
                disease_id=row.disease_id,
                disease_name=row.disease_name,
                disease_category=row.disease_category,
                association_type=row.association_type,
                confidence_score=row.confidence_score,
            ))
            if row.association_type == 'known':
                known_count += 1
            else:
                predicted_count += 1
        
        return DrugAssociationsListResponse(
            drug_id=drug.id,
            drug_name=drug.name,
            associations=associations,
            total=len(associations),
            known_count=known_count,
            predicted_count=predicted_count,
        )
    
    async def get_drug_statistics(self) -> DrugStatisticsResponse:
        """
        Get overall drug statistics.
        
        Returns:
            Statistics about drugs and their associations
        """
        # Total drugs
        total_query = "SELECT COUNT(*) FROM drugs"
        total_result = await self.db.execute(text(total_query))
        total_drugs = total_result.scalar() or 0
        
        # Drugs with associations
        with_assoc_query = """
            SELECT COUNT(DISTINCT drug_id) 
            FROM drug_disease_associations
        """
        with_assoc_result = await self.db.execute(text(with_assoc_query))
        drugs_with_associations = with_assoc_result.scalar() or 0
        
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
        
        # Type distribution
        type_query = """
            SELECT type, COUNT(*) as count
            FROM drugs
            WHERE type IS NOT NULL
            GROUP BY type
            ORDER BY count DESC
        """
        type_result = await self.db.execute(text(type_query))
        type_distribution = [
            {"type": row.type, "count": row.count}
            for row in type_result.fetchall()
        ]
        
        # Top associated drugs
        top_query = """
            SELECT d.id, d.name, d.type, COUNT(dda.id) as association_count
            FROM drugs d
            JOIN drug_disease_associations dda ON d.id = dda.drug_id
            GROUP BY d.id, d.name, d.type
            ORDER BY association_count DESC
            LIMIT 10
        """
        top_result = await self.db.execute(text(top_query))
        top_associated_drugs = [
            {
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "association_count": row.association_count
            }
            for row in top_result.fetchall()
        ]
        
        return DrugStatisticsResponse(
            total_drugs=total_drugs,
            drugs_with_associations=drugs_with_associations,
            total_associations=assoc_row.total or 0 if assoc_row else 0,
            known_associations=assoc_row.known or 0 if assoc_row else 0,
            predicted_associations=assoc_row.predicted or 0 if assoc_row else 0,
            type_distribution=type_distribution,
            top_associated_drugs=top_associated_drugs,
        )
    
    async def get_drug_types(self) -> List[str]:
        """Get list of all drug types."""
        query = """
            SELECT DISTINCT type 
            FROM drugs 
            WHERE type IS NOT NULL 
            ORDER BY type
        """
        result = await self.db.execute(text(query))
        return [row.type for row in result.fetchall()]
