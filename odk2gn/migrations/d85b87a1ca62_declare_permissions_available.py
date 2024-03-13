"""declare permissions available

Revision ID: d85b87a1ca62
Revises: 7a49e76756df
Create Date: 2024-03-13 16:26:32.471062

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d85b87a1ca62"
down_revision = "7a49e76756df"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO
            gn_permissions.t_permissions_available (
                id_module,
                id_object,
                id_action,
                label,
                scope_filter,
                sensitivity_filter
            )
        SELECT
            m.id_module,
            o.id_object,
            a.id_action,
            v.label,
            v.scope_filter,
            v.sensitivity_filter
        FROM
            (
                VALUES
                     ('ADMIN', 'ODK2GN', 'C', False, False, 'Créer des formulaires ODK')
                    ,('ADMIN', 'ODK2GN', 'R', False, False, 'Voir des formulaires ODK')
                    ,('ADMIN', 'ODK2GN', 'U', False, False, 'Modifier des formulaires ODK')
                    ,('ADMIN', 'ODK2GN', 'E', False, False, 'Exporter des formulaires ODK')
                    ,('ADMIN', 'ODK2GN', 'D', False, False, 'Supprimer des formulaires ODK')
            ) AS v (module_code, object_code, action_code, scope_filter, sensitivity_filter, label)
        JOIN
            gn_commons.t_modules m ON m.module_code = v.module_code
        JOIN
            gn_permissions.t_objects o ON o.code_object = v.object_code
        JOIN
            gn_permissions.bib_actions a ON a.code_action = v.action_code;
    
        INSERT INTO
            gn_permissions.t_permissions (
                id_role,
                id_action,
                id_module,
                id_object,
                sensitivity_filter
            )
        SELECT
        	r.id_role,
            a.id_action,
            m.id_module,
            o.id_object,
            v.sensitivity_filter
        FROM
            (
                VALUES
                     ('Grp_admin', 'C', 'ADMIN', 'ODK2GN','False')
                    ,('Grp_admin', 'R', 'ADMIN', 'ODK2GN','False')
                    ,('Grp_admin', 'U', 'ADMIN', 'ODK2GN','False')
                    ,('Grp_admin', 'E', 'ADMIN', 'ODK2GN','False')
                    ,('Grp_admin', 'D', 'ADMIN', 'ODK2GN','False')
            ) AS v (role_nom, action_code, module_code, object_code, sensitivity_filter)
        JOIN
            gn_commons.t_modules m ON m.module_code = v.module_code
        JOIN
            gn_permissions.t_objects o ON o.code_object = v.object_code
        JOIN
            gn_permissions.bib_actions a ON a.code_action = v.action_code
        JOIN
            utilisateurs.t_roles r ON r.nom_role = v.role_nom; 
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.t_permissions
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN');
        DELETE FROM gn_permissions.t_permissions_available
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN');
        """
    )
