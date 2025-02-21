"""add ODK2GN available permissions

Revision ID: 7aac4c08483b
Revises: 7a49e76756df
Create Date: 2025-02-21 16:37:53.652049

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7aac4c08483b"
down_revision = "7a49e76756df"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_permissions.t_permissions_available
        (id_module, id_object, id_action, "label", scope_filter, sensitivity_filter)
        SELECT 
        (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
        (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
        ba.id_action, ba.description_action, FALSE, false
        FROM gn_permissions.bib_actions ba; 
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.t_permissions_available 
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN')
            AND id_module = (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'); 
        DELETE FROM gn_permissions.t_permissions 
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN')
            AND id_module = (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'); 
        """
    )
