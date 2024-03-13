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
        INSERT INTO gn_permissions.t_permissions_available (id_module,id_object,id_action,label,scope_filter,sensitivity_filter)
        VALUES(
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'C'),
            'Créer des formulaires ODK',
            'false',
            'false'
            );
        INSERT INTO gn_permissions.t_permissions_available (id_module,id_object,id_action,label,scope_filter,sensitivity_filter)
        VALUES(
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'R'),
            'Voir des formulaires ODK',
            'false',
            'false'
            );
        INSERT INTO gn_permissions.t_permissions_available (id_module,id_object,id_action,label,scope_filter,sensitivity_filter)
        VALUES(
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'U'),
            'Modifier des formulaires ODK',
            'false',
            'false'
            );
        INSERT INTO gn_permissions.t_permissions_available (id_module,id_object,id_action,label,scope_filter,sensitivity_filter)
        VALUES(
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'E'),
            'Exporter des formulaires ODK',
            'false',
            'false'
            );
        INSERT INTO gn_permissions.t_permissions_available (id_module,id_object,id_action,label,scope_filter,sensitivity_filter)
        VALUES(
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'D'),
            'Supprimer des formulaires ODK',
            'false',
            'false'
            );
        INSERT INTO gn_permissions.t_permissions (id_role,id_action,id_module,id_object,sensitivity_filter)
        VALUES(
            (SELECT id_role FROM utilisateurs.t_roles WHERE nom_role = 'Grp_admin'), 
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'C'),
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            'false'
            );
        INSERT INTO gn_permissions.t_permissions (id_role,id_action,id_module,id_object,sensitivity_filter)
        VALUES(
            (SELECT id_role FROM utilisateurs.t_roles WHERE nom_role = 'Grp_admin'), 
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'R'),
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            'false'
            );
         INSERT INTO gn_permissions.t_permissions (id_role,id_action,id_module,id_object,sensitivity_filter)
        VALUES(
            (SELECT id_role FROM utilisateurs.t_roles WHERE nom_role = 'Grp_admin'), 
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'U'),
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            'false'
            );
        INSERT INTO gn_permissions.t_permissions (id_role,id_action,id_module,id_object,sensitivity_filter)
        VALUES(
            (SELECT id_role FROM utilisateurs.t_roles WHERE nom_role = 'Grp_admin'), 
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'E'),
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            'false'
            );
        INSERT INTO gn_permissions.t_permissions (id_role,id_action,id_module,id_object,sensitivity_filter)
        VALUES(
            (SELECT id_role FROM utilisateurs.t_roles WHERE nom_role = 'Grp_admin'), 
            (SELECT id_action FROM gn_permissions.bib_actions WHERE code_action = 'D'),
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'ADMIN'), 
            (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN'),
            'false'
            );
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.t_permissions
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN');
        DELETE FROM gn_permissions.t_permissions_available
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN');
        DELETE FROM gn_permissions.cor_object_module 
        WHERE id_object in (SELECT id_object FROM gn_permissions.t_objects WHERE code_object = 'ODK2GN');
        DELETE FROM gn_permissions.t_objects
        WHERE code_object = 'ODK2GN';
        """
    )
