"""init odk2gn

Revision ID: c1fa7f243102
Revises: 1b4f44762020
Create Date: 2023-07-24 12:08:05.102285

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1fa7f243102"
down_revision = None
branch_labels = ("odk2gn",)
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE SCHEMA odk2gn;

        CREATE TABLE odk2gn.t_odk_forms(
        id SERIAL NOT NULL,
        odk_form_id varchar(255) NOT NULL,
        odk_project_id INTEGER NOT NULL,
        id_module INTEGER,
        
        CONSTRAINT pk_t_odk_forms PRIMARY KEY (id),
        CONSTRAINT fk_t_odk_forms_id_module FOREIGN KEY (id_module)
            REFERENCES gn_commons.t_modules (id_module) MATCH SIMPLE
            ON UPDATE CASCADE ON DELETE CASCADE
        );


        """
    )


def downgrade():
    op.execute(
        """
    DROP TABLE odk2gn.t_odk_forms;

    DROP SCHEMA odk2gn;
    """
    )
