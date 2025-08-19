"""ativo InvestmentPlan

Revision ID: e211da060695
Revises: 25655aa91cff
Create Date: 2025-08-06 01:08:34.928411

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e211da060695'
down_revision = '25655aa91cff'
branch_labels = None
depends_on = None


def upgrade():
    # Passo 1: adiciona a coluna permitindo NULL temporariamente
    with op.batch_alter_table('investment_plan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ativo', sa.Boolean(), nullable=True))

    # Passo 2: define todos os registros existentes como inativos (False)
    op.execute("UPDATE investment_plan SET ativo = FALSE")

    # Passo 3: torna a coluna obrigatória (NOT NULL)
    with op.batch_alter_table('investment_plan', schema=None) as batch_op:
        batch_op.alter_column('ativo',
                              existing_type=sa.Boolean(),
                              nullable=False)

