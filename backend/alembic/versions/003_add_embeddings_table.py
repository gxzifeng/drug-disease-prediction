"""Add embeddings table

Revision ID: 003
Revises: 002
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'embeddings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('graph_id', sa.Integer(), nullable=False),
        sa.Column('algorithm', sa.String(length=50), nullable=False),
        sa.Column('embedding_dim', sa.Integer(), nullable=False, default=64),
        sa.Column('epochs', sa.Integer(), default=100),
        sa.Column('learning_rate', sa.Float(), default=0.01),
        sa.Column('random_seed', sa.Integer(), default=42),
        sa.Column('node2vec_params', sa.JSON(), nullable=True),
        sa.Column('gcn_params', sa.JSON(), nullable=True),
        sa.Column('training_loss', sa.Float(), nullable=True),
        sa.Column('val_loss', sa.Float(), nullable=True),
        sa.Column('training_time_seconds', sa.Float(), nullable=True),
        sa.Column('training_history', sa.JSON(), nullable=True),
        sa.Column('embedding_path', sa.String(length=500), nullable=True),
        sa.Column('model_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), default='pending'),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_id', sa.String(length=100), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['graph_id'], ['graphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_embeddings_name'), 'embeddings', ['name'], unique=False)
    op.create_index(op.f('ix_embeddings_graph_id'), 'embeddings', ['graph_id'], unique=False)
    op.create_index(op.f('ix_embeddings_algorithm'), 'embeddings', ['algorithm'], unique=False)
    op.create_index(op.f('ix_embeddings_task_id'), 'embeddings', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_embeddings_task_id'), table_name='embeddings')
    op.drop_index(op.f('ix_embeddings_algorithm'), table_name='embeddings')
    op.drop_index(op.f('ix_embeddings_graph_id'), table_name='embeddings')
    op.drop_index(op.f('ix_embeddings_name'), table_name='embeddings')
    op.drop_table('embeddings')
