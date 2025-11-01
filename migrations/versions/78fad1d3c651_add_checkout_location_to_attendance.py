"""add_checkout_location_to_attendance

Revision ID: 78fad1d3c651
Revises: 4200751b68b6
Create Date: 2025-11-01 07:02:14.648066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78fad1d3c651'
down_revision = '4200751b68b6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lat_out', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('lng_out', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('address_out', sa.String(length=256), nullable=True))

def downgrade():
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.drop_column('address_out')
        batch_op.drop_column('lng_out')
        batch_op.drop_column('lat_out')
