import logging
import click
import uuid

import flatdict
from flask import has_app_context

from sqlalchemy.orm import exc
from sqlalchemy.exc import SQLAlchemyError

from geonature.app import create_app
from geonature.utils.env import BACKEND_DIR
from geonature.core.gn_commons.models import BibTablesLocation
from pypnnomenclature.models import TNomenclatures
from gn_module_monitoring.monitoring.models import TMonitoringSites
from geonature.core.gn_monitoring.models import TBaseSites
from gn_module_monitoring.config.repositories import get_config
from geonature.utils.utilsmails import send_mail
from geonature.core.gn_commons.models import TMedias
from pypnusershub.db.models import User

from geonature.utils.env import DB

from odk2gn.config import config
from odk2gn.odk_api import (
    get_submissions,
    update_form_attachment,
    get_attachment,
    ODKSchema,
    update_review_state,
)
from odk2gn.monitoring_utils import parse_and_create_visit, parse_and_create_obs
from odk2gn.config_schema import ProcoleSchema

from odk2gn.gn2_utils import get_modules_info, get_gn2_attachments_data

# TODO : post visite

import pprint

log = logging.getLogger("app")
log.setLevel(logging.INFO)
pp = pprint.PrettyPrinter(width=41, compact=True)

# with client:
#     schema = ODKSchema(4, "form_workshop")
#     field = schema.get_field_info("toto")
#     print(field)
#     # schema = get_schema_fields(4, "form_workshop")
#     pp.pprint(schema)


@click.group()
def synchronize():
    # For testing we mock an app with an already context pushed
    # we push app context only if it's not done
    app = create_app()
    if not has_app_context():
        app.app_context().push()


@click.group()
def upgrade_odk_form():
    app = create_app()
    if not has_app_context():
        app.app_context().push()


@click.command("test")
def test():
    fetched_module = get_modules_info("MODULE_1")
    click.echo("Beau test")


@click.command()
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def get_schema(project_id, form_id):
    odk_schema = ODKSchema(project_id, form_id)
    pp.pprint(odk_schema.schema)


def get_and_post_medium(
    project_id,
    form_id,
    uuid_sub,
    filename,
    monitoring_table,
    media_type,
    uuid_gn_object,
):
    # TODO : remove app context
    img = get_attachment(project_id, form_id, uuid_sub, filename)
    if img:
        uuid_sub = uuid_sub.split(":")[1]
        medias_name = f"{uuid_sub}_{filename}"
        table_location = (
            DB.session.query(BibTablesLocation)
            .filter_by(
                schema_name="gn_monitoring",
                table_name=monitoring_table,
            )
            .one()
        )
        media_type = (
            DB.session.query(TNomenclatures)
            .filter_by(mnemonique=media_type)
            .filter(TNomenclatures.nomenclature_type.has(mnemonique="TYPE_MEDIA"))
            .one()
        )
        media = {
            "media_path": f"media/attachments/{medias_name}",
            "uuid_attached_row": uuid_gn_object,
            "id_table_location": table_location.id_table_location,
            "id_nomenclature_media_type": media_type.id_nomenclature,
        }

        media = TMedias(**media)
        DB.session.add(media)
        DB.session.commit()
        with open(BACKEND_DIR / "media" / "attachments" / medias_name, "wb") as out_file:
            out_file.write(img.content)


@synchronize.command(name="monitoring")
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def synchronize_monitoring(module_code, project_id, form_id):
    odk_form_schema = ODKSchema(project_id, form_id)

    log.info(f"--- Start synchro for module {module_code} ---")
    try:
        module_parser_config = config[module_code]
    except KeyError as e:
        log.warning(
            f"No mapping found for module {module_code} - get the default ODK monitoring template mapping !  "
        )
        module_parser_config = {}
    module_parser_config = ProcoleSchema().load(module_parser_config)
    gn_module = get_modules_info(module_code)

    monitoring_config = get_config(module_code)
    form_data = get_submissions(project_id, form_id)
    for sub in form_data:
        flatten_data = flatdict.FlatDict(sub, delimiter="/")
        observations_list = []

        try:
            observations_list = flatten_data.pop(
                module_parser_config["OBSERVATION"]["observations_repeat"]
            )

            assert type(observations_list) is list
        except KeyError:
            log.warning("No observation for this visit")
        except AssertionError:
            log.error("Observation node is not a list")
            raise

        visit = parse_and_create_visit(
            flatten_data,
            module_parser_config,
            monitoring_config,
            gn_module,
            odk_form_schema,
        )

        get_and_post_medium(
            project_id=project_id,
            form_id=form_id,
            uuid_sub=flatten_data.get("meta/instanceID"),
            filename=flatten_data.get(module_parser_config["VISIT"]["media"]),
            monitoring_table="t_base_visits",
            media_type=module_parser_config["VISIT"]["media_type"],
            uuid_gn_object=visit.uuid_base_visit,
        )

        for obs in observations_list:
            gn_uuid_obs = uuid.uuid4()
            flatten_obs = flatdict.FlatDict(obs, delimiter="/")

            observation = parse_and_create_obs(
                flatten_obs,
                module_parser_config,
                monitoring_config,
                odk_form_schema,
                gn_uuid_obs,
            )

            get_and_post_medium(
                project_id=project_id,
                form_id=form_id,
                uuid_sub=flatten_data.get("meta/instanceID"),
                filename=flatten_obs.get(module_parser_config["OBSERVATION"]["media"]),
                monitoring_table="t_observations",
                media_type=module_parser_config["OBSERVATION"]["media_type"],
                uuid_gn_object=gn_uuid_obs,
            )
            visit.observations.append(observation)
        DB.session.add(visit)
        try:
            DB.session.commit()
            update_review_state(project_id, form_id, sub["__id"], "approved")

        except SQLAlchemyError as e:
            log.error("Error while posting data")
            log.error(str(e))
            send_mail(
                config["gn_odk"]["email_for_error"],
                subject="Synchronisation ODK error",
                msg_html=str(e),
            )
            update_review_state(project_id, form_id, sub["__id"], "hasIssues")
            DB.session.rollback()
    log.info(f"--- Finish synchronize for module {module_code} ---")


@upgrade_odk_form.command(name="monitoring")
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
@click.option("--skip_taxons", is_flag=True, help="Skip taxon sync.")
@click.option("--skip_observers", is_flag=True, help="Skip observers sync.")
@click.option("--skip_jdd", is_flag=True, help="Skip jdd sync.")
@click.option("--skip_sites", is_flag=True, help="Skip sites sync.")
@click.option("--skip_nomenclatures", is_flag=True, help="Skip nomenclatures sync.")
def upgrade_monitoring(
    module_code,
    project_id,
    form_id,
    skip_taxons,
    skip_observers,
    skip_jdd,
    skip_sites,
    skip_nomenclatures,
):
    log.info(f"--- Start upgrade form for module {module_code} ---")
    module = get_modules_info(module_code=module_code)

    # Get gn2 attachments data
    files = get_gn2_attachments_data(
        module=module,
        skip_taxons=skip_taxons,
        skip_observers=skip_observers,
        skip_jdd=skip_jdd,
        skip_sites=skip_sites,
        skip_nomenclatures=skip_nomenclatures,
    )
    # Update form
    update_form_attachment(project_id=project_id, xml_form_id=form_id, files=files)
    log.info(f"--- Done ---")
