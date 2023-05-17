import click
from odk_flore_prioritaire.odk_methods import update_odk_form, update_priority_flora_db
from odk2gn.main import synchronize, upgrade_odk_form
from geonature.app import create_app


@synchronize.command(name="flore-prio")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def synchronize(project_id, form_id):
    update_priority_flora_db(project_id=project_id, form_id=form_id)


@upgrade_odk_form.command(name="flore-prio")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def upgrade_odk_form(project_id, form_id):
    app = create_app()
    with app.app_context() as app_ctx:
        update_odk_form(project_id=project_id, form_id=form_id)
