"""ML models and predictions tables

Revision ID: 007
Revises: 006
Create Date: 2025-01-24 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ML models and predictions tables."""

    # Create ml_models table
    op.create_table(
        'ml_models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('model_type', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default="'training'"),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('feature_names', JSONB, nullable=False, server_default='[]'),
        sa.Column('hyperparameters', JSONB, nullable=False, server_default='{}'),
        sa.Column('metrics', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('trained_at', sa.DateTime(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id')
    )

    # Create indexes for ml_models
    op.create_index('ix_ml_models_model_id', 'ml_models', ['model_id'], unique=True)
    op.create_index('ix_ml_models_model_name', 'ml_models', ['model_name'])
    op.create_index('ix_ml_models_status', 'ml_models', ['status'])
    op.create_index('ix_ml_models_created_at', 'ml_models', ['created_at'])

    # Create ml_predictions table
    op.create_table(
        'ml_predictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('prediction_id', sa.String(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('prediction_value', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('probabilities', JSONB, nullable=False, server_default='{}'),
        sa.Column('features', JSONB, nullable=False, server_default='{}'),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('predicted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prediction_id')
    )

    # Create indexes for ml_predictions
    op.create_index('ix_ml_predictions_prediction_id', 'ml_predictions', ['prediction_id'], unique=True)
    op.create_index('ix_ml_predictions_model_id', 'ml_predictions', ['model_id'])
    op.create_index('ix_ml_predictions_model_name', 'ml_predictions', ['model_name'])
    op.create_index('ix_ml_predictions_entity_type', 'ml_predictions', ['entity_type'])
    op.create_index('ix_ml_predictions_entity_id', 'ml_predictions', ['entity_id'])
    op.create_index('ix_ml_predictions_predicted_at', 'ml_predictions', ['predicted_at'])


def downgrade() -> None:
    """Drop ML tables."""

    # Drop indexes for ml_predictions
    op.drop_index('ix_ml_predictions_predicted_at', table_name='ml_predictions')
    op.drop_index('ix_ml_predictions_entity_id', table_name='ml_predictions')
    op.drop_index('ix_ml_predictions_entity_type', table_name='ml_predictions')
    op.drop_index('ix_ml_predictions_model_name', table_name='ml_predictions')
    op.drop_index('ix_ml_predictions_model_id', table_name='ml_predictions')
    op.drop_index('ix_ml_predictions_prediction_id', table_name='ml_predictions')

    # Drop ml_predictions table
    op.drop_table('ml_predictions')

    # Drop indexes for ml_models
    op.drop_index('ix_ml_models_created_at', table_name='ml_models')
    op.drop_index('ix_ml_models_status', table_name='ml_models')
    op.drop_index('ix_ml_models_model_name', table_name='ml_models')
    op.drop_index('ix_ml_models_model_id', table_name='ml_models')

    # Drop ml_models table
    op.drop_table('ml_models')
