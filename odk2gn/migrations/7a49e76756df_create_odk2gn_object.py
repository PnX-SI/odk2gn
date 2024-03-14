"""create odk2gn object

Revision ID: 7a49e76756df
Revises: c1fa7f243102
Create Date: 2023-08-10 10:31:03.903793

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a49e76756df"
down_revision = "c1fa7f243102"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_permissions.t_objects (code_object, description_object)
        VALUES ('ODK2GN', 'Permissions sur odk2gn');
        INSERT INTO gn_permissions.cor_object_module (id_object, id_module)
        VALUES((SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'), 
                (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'));

        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.cor_object_module 
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN');
        DELETE FROM gn_permissions.t_objects
        WHERE code_object = 'ODK2GN';
        """
    )
