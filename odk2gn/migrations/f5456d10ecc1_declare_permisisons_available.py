"""declare permisisons available

Revision ID: f5456d10ecc1
Revises: 7a49e76756df
Create Date: 2024-03-13 14:25:12.455405

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5456d10ecc1'
down_revision = '7a49e76756df'
branch_labels = None
depends_on = None


def upgrade():
   
   op.execute(
    """
    DELETE FROM gn_permissions.cor_object_module
    where id_object = (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN')
    and id_module =  (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN');
    DELETE FROM gn_permissions.t_objects
    where id_object = (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN')
    ;

        INSERT INTO gn_permissions.t_objects (code_object, description_object)
        VALUES ('ODK2GN_SYNCHRO', 'Synchronisation odk2gn');
        INSERT INTO gn_permissions.cor_object_module (id_object, id_module)
        VALUES((SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN_SYNCHRO'), 
                (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ODK2GN'));
    """
   )
   op.execute(
        """
        INSERT INTO
            gn_permissions.t_permissions_available (
                id_module,
                id_object,
                id_action,
                label,
                scope_filter
            )
        SELECT
            m.id_module,
            o.id_object,
            a.id_action,
            v.label,
            v.scope_filter
        FROM
            (
                VALUES
                     ('ODK2GN', 'ODK2GN_SYNCHRO', 'C', False, 'Créer une synchro'),
                     ('ODK2GN', 'ODK2GN_SYNCHRO', 'R', False, 'Lire les synchro'),
                     ('ODK2GN', 'ODK2GN_SYNCHRO', 'U', False, 'Mettre à jour une synchro'),
                     ('ODK2GN', 'ODK2GN_SYNCHRO', 'D', False, 'Supprimer une synchro')
            ) AS v (module_code, object_code, action_code, scope_filter, label)
        JOIN
            gn_commons.t_modules m ON m.module_code = v.module_code
        JOIN
            gn_permissions.t_objects o ON o.code_object = v.object_code
        JOIN
            gn_permissions.bib_actions a ON a.code_action = v.action_code
        """
    )

def downgrade():

    op.execute(
    """
    DELETE FROM gn_permissions.t_permissions
    WHERE id_module = (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ODK2GN');
    
    DELETE FROM gn_permissions.t_permissions_available
    WHERE id_module = (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ODK2GN');

    DELETE FROM gn_permissions.cor_object_module
    where id_object = (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN_SYNCHRO')
    and id_module =  (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ODK2GN');
    DELETE FROM gn_permissions.t_objects
    where id_object = (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN_SYNCHRO')
    ;

    INSERT INTO gn_permissions.t_objects (code_object, description_object)
    VALUES ('ODK2GN', 'Permissions sur odk2gn');
    INSERT INTO gn_permissions.cor_object_module (id_object, id_module)
    VALUES((SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'), 
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'));
    """
    )
    op.execute(
    """
    DELETE FROM gn_permissions.t_permissions_available
    WHERE id_object = (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN')
    """
    )
