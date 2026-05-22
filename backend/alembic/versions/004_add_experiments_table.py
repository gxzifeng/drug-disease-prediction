"""Add experiments table

Revision ID: 004
Revises: 003
Create Date: 2026-01-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding_id', sa.Integer(), nullable=False),
        sa.Column('classifier', sa.String(length=50), nullable=False),
        sa.Column('feature_method', sa.String(length=50), nullable=False, server_default='concat'),
        sa.Column('random_seed', sa.Integer(), nullable=True, server_default='42'),
        sa.Column('test_size', sa.Float(), nullable=True, server_default='0.2'),
        sa.Column('k_fold', sa.Integer(), nullable=True),
        sa.Column('classifier_params', sa.JSON(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('auc_roc', sa.Float(), nullable=True),
        sa.Column('auc_pr', sa.Float(), nullable=True),
        sa.Column('kfold_metrics', sa.JSON(), nullable=True),
        sa.Column('feature_importance', sa.JSON(), nullable=True),
        sa.Column('confusion_matrix', sa.JSON(), nullable=True),
        sa.Column('training_time_seconds', sa.Float(), nullable=True),
        sa.Column('num_train_samples', sa.Integer(), nullable=True),
        sa.Column('num_test_samples', sa.Integer(), nullable=True),
        sa.Column('num_features', sa.Integer(), nullable=True),
        sa.Column('model_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_id', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['embedding_id'], ['embeddings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_experiments_name'), 'experiments', ['name'], unique=False)
    op.create_index(op.f('ix_experiments_embedding_id'), 'experiments', ['embedding_id'], unique=False)
    op.create_index(op.f('ix_experiments_classifier'), 'experiments', ['classifier'], unique=False)
    op.create_index(op.f('ix_experiments_task_id'), 'experiments', ['task_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_experiments_task_id'), table_name='experiments')
    op.drop_index(op.f('ix_experiments_classifier'), table_name='experiments')
    op.drop_index(op.f('ix_experiments_embedding_id'), table_name='experiments')
    op.drop_index(op.f('ix_experiments_name'), table_name='experiments')
    
    # Drop table
    op.drop_table('experiments')
