"""add graphs table

Revision ID: 002
Revises: 001
Create Date: 2026-01-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'graphs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('negative_sample_ratio', sa.Float(), nullable=False, default=1.0),
        sa.Column('train_ratio', sa.Float(), nullable=False, default=0.7),
        sa.Column('val_ratio', sa.Float(), nullable=False, default=0.15),
        sa.Column('test_ratio', sa.Float(), nullable=False, default=0.15),
        sa.Column('random_seed', sa.Integer(), nullable=False, default=42),
        sa.Column('num_drug_nodes', sa.Integer(), nullable=False, default=0),
        sa.Column('num_disease_nodes', sa.Integer(), nullable=False, default=0),
        sa.Column('num_total_nodes', sa.Integer(), nullable=False, default=0),
        sa.Column('num_edges', sa.Integer(), nullable=False, default=0),
        sa.Column('num_positive_edges', sa.Integer(), nullable=False, default=0),
        sa.Column('num_negative_edges', sa.Integer(), nullable=False, default=0),
        sa.Column('num_train_edges', sa.Integer(), nullable=False, default=0),
        sa.Column('num_val_edges', sa.Integer(), nullable=False, default=0),
        sa.Column('num_test_edges', sa.Integer(), nullable=False, default=0),
        sa.Column('node_index_path', sa.String(length=500), nullable=True),
        sa.Column('edge_index_path', sa.String(length=500), nullable=True),
        sa.Column('train_mask_path', sa.String(length=500), nullable=True),
        sa.Column('val_mask_path', sa.String(length=500), nullable=True),
        sa.Column('test_mask_path', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('is_built', sa.Boolean(), nullable=False, default=False),
        sa.Column('build_error', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_graphs_name'), 'graphs', ['name'], unique=False)
    op.create_index(op.f('ix_graphs_dataset_id'), 'graphs', ['dataset_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_graphs_dataset_id'), table_name='graphs')
    op.drop_index(op.f('ix_graphs_name'), table_name='graphs')
    op.drop_table('graphs')
