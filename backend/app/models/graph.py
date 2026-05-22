"""Graph database model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Graph(Base):
    """Graph model for storing drug-disease bipartite graph data."""

    __tablename__ = "graphs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source dataset
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Graph build parameters
    negative_sample_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    train_ratio: Mapped[float] = mapped_column(Float, default=0.7)
    val_ratio: Mapped[float] = mapped_column(Float, default=0.15)
    test_ratio: Mapped[float] = mapped_column(Float, default=0.15)
    random_seed: Mapped[int] = mapped_column(Integer, default=42)

    # Graph statistics
    num_drug_nodes: Mapped[int] = mapped_column(Integer, default=0)
    num_disease_nodes: Mapped[int] = mapped_column(Integer, default=0)
    num_total_nodes: Mapped[int] = mapped_column(Integer, default=0)
    num_edges: Mapped[int] = mapped_column(Integer, default=0)
    num_positive_edges: Mapped[int] = mapped_column(Integer, default=0)
    num_negative_edges: Mapped[int] = mapped_column(Integer, default=0)

    # Split statistics
    num_train_edges: Mapped[int] = mapped_column(Integer, default=0)
    num_val_edges: Mapped[int] = mapped_column(Integer, default=0)
    num_test_edges: Mapped[int] = mapped_column(Integer, default=0)

    # File paths for graph artifacts
    node_index_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    edge_index_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    train_mask_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    val_mask_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    test_mask_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Additional metadata stored as JSON
    graph_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Audit fields
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    dataset = relationship("Dataset", foreign_keys=[dataset_id])
    creator = relationship("User", foreign_keys=[created_by])

    @property
    def is_built(self) -> bool:
        """
        Graph build status.

        说明：
        - 当前数据库表未显式持久化 `is_built` 字段（历史原因），因此用 `graph_metadata` 兜底存储。
        - 同时兼容根据产物路径推断构建状态。
        """
        if isinstance(self.graph_metadata, dict) and "is_built" in self.graph_metadata:
            return bool(self.graph_metadata.get("is_built"))
        # Fallback: infer from artifact paths
        return bool(
            self.node_index_path
            and self.edge_index_path
            and self.train_mask_path
            and self.val_mask_path
            and self.test_mask_path
        )

    @is_built.setter
    def is_built(self, value: bool) -> None:
        meta = self.graph_metadata if isinstance(self.graph_metadata, dict) else {}
        meta["is_built"] = bool(value)
        # 清空错误信息（成功时）
        if value:
            meta.pop("build_error", None)
        self.graph_metadata = meta

    @property
    def build_error(self) -> Optional[str]:
        """Build error message (stored in graph_metadata for compatibility)."""
        if isinstance(self.graph_metadata, dict):
            v = self.graph_metadata.get("build_error")
            return str(v) if v is not None else None
        return None

    @build_error.setter
    def build_error(self, value: Optional[str]) -> None:
        meta = self.graph_metadata if isinstance(self.graph_metadata, dict) else {}
        meta["build_error"] = value
        self.graph_metadata = meta

    def __repr__(self) -> str:
        return f"<Graph {self.name} (id={self.id}, dataset_id={self.dataset_id})>"
