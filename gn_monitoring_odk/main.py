import logging
import click
import uuid

import flatdict
from sqlalchemy.orm import exc

from geonature.app import create_app
from geonature.utils.env import BACKEND_DIR
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_commons.models import BibTablesLocation
from pypnnomenclature.models import TNomenclatures

from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
)
from gn_module_monitoring.config.repositories import get_config
from geonature.utils.utilsmails import send_mail
from geonature.core.gn_commons.models import TMedias
from pypnusershub.db.models import User

from geonature.utils.env import DB

from gn_monitoring_odk.config import config
from gn_monitoring_odk.odk_api import (
    get_submissions,
    update_form_attachment,
    get_attachments,
    get_attachment,
    client,
    ODKSchema,
)
from gn_monitoring_odk.utils_dict import NestedDictAccessor
from gn_monitoring_odk.config_schema import ProcoleSchema

from gn_monitoring_odk.gn2_utils import (
    get_modules_info,
    get_gn2_attachments_data
)

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


def get_and_post_medium(
    project_id,
    form_id,
    uuid_sub,
    filename,
    monitoring_table,
    media_type,
    uuid_gn_object,
):
    app = create_app()
    with app.app_context():
        img = get_attachment(project_id, form_id, uuid_sub, filename)
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
            "media_path": f"static/medias/{medias_name}",
            "uuid_attached_row": uuid_gn_object,
            "id_table_location": table_location.id_table_location,
            "id_nomenclature_media_type": media_type.id_nomenclature,
        }

        media = TMedias(**media)
        DB.session.add(media)
        DB.session.commit()
        with open(BACKEND_DIR / "static" / "medias" / medias_name, "wb") as out_file:
            out_file.write(img.content)


@click.command()
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def synchronize(module_code, project_id, form_id):
    odk_form_schema = ODKSchema(project_id, form_id)
    app = create_app()
    with app.app_context() as app_ctx:
        log.info(f"--- Start synchro for module {module_code} ---")
        try:
            schema = config[module_code]
        except KeyError as e:
            log.error(f"No configuration found for module {module_code} ")
            raise
        ProcoleSchema().load(schema)
        try:
            gn_module = (
                DB.session.query(TModules)
                .filter_by(module_code=module_code.lower())
                .one()
            )
        except (exc.NoResultFound) as e:
            log.error(f"No GeoNature module found for {module_code.lower()}")
            raise
        monitoring_config = get_config(module_code.lower())
        # pp.pprint(monitoring_config["visit"]["generic"].keys())
        # pp.pprint(monitoring_config["visit"]["specific"].keys())
        visit_default_column = monitoring_config["visit"]["generic"].keys()
        visit_json_columns = monitoring_config["visit"]["specific"].keys()
        observation_default_column = monitoring_config["observation"]["generic"].keys()
        observation_json_columns = monitoring_config["observation"]["specific"].keys()
        pp.pprint(monitoring_config["observation"]["specific"].keys())
        form_data = get_submissions(project_id, form_id)
        # pp.pprint(form_data)
        for sub in form_data:
            sites = DB.session.query(TMonitoringSites).all()
            visite = TMonitoringVisits(
                id_base_site=1,
                id_dataset=9742,
                id_module=1368,
                visit_date_min=datetime.now(),
                visit_date_max=datetime.now(),
                comments="toto",
                data={"debutant": "Oui", "nuages": "0-33%"},
                observers=DB.session.query(User).all(),
            )

            observation = TMonitoringObservations(
                cd_nom=2975, comments="super obs", data={"nb_0_5": 5, "nb_5_10": 2}
            )

            visite.observations.append(observation)

            DB.session.add(visite)

            try:
                DB.session.commit()
                pass
            except exc.SQLAlchemyError as e:
                send_mail(
                    config["gn_odk"]["email_for_error"],
                    subject="Synchronisation ODK error",
                    msg_html=str(e),
                )
                DB.session.rollback()

            # try:
            #     DB.session.commit()
            #     pass
            # except exc.SQLAlchemyError as e:
            #     send_mail(
            #         config["gn_odk"]["email_for_error"],
            #         subject="Synchronisation ODK error",
            #         msg_html=str(e),
            #     )
            #     DB.session.rollback()


@click.command()
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def upgrade_odk_form(module_code, project_id, form_id):
    log.info(f"--- Start upgrade form for module {module_code} ---")

    app = create_app()

    with app.app_context() as app_ctx:
        # Get Module
        module = get_modules_info(module_code=module_code)
        # Get gn2 attachments data
        files = get_gn2_attachments_data(module=module, id_nomeclature_type=[])
        # Update form
        update_form_attachment(project_id=project_id, xml_form_id=form_id, files=files)
    log.info(f"--- Done ---")
