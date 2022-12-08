import logging
import click
import uuid

import flatdict
from sqlalchemy.orm import exc
from sqlalchemy.exc import SQLAlchemyError

from geonature.app import create_app
from geonature.utils.env import BACKEND_DIR
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
    ODKSchema,
)
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
            module_config = config[module_code]
        except KeyError as e:
            log.error(f"No configuration found for module {module_code} ")
            raise
        module_config = ProcoleSchema().load(module_config)
        gn_module = get_modules_info(module_code)
        monitoring_config = get_config(module_code.lower())
        visit_generic_column = monitoring_config["visit"]["generic"].keys()
        visit_specific_column = monitoring_config["visit"]["specific"].keys()
        observation_generic_column = monitoring_config["observation"]["generic"].keys()
        observation_specific_column = monitoring_config["observation"][
            "specific"
        ].keys()
        form_data = get_submissions(project_id, form_id)
        print("NB SUB", len(form_data))
        for sub in form_data:
            pp.pprint(sub)
            flatten_data = flatdict.FlatDict(sub, delimiter="/")
            observation_data = []
            try:
                observation_data = flatten_data.pop(
                    module_config["OBSERVATION"]["path"]
                )
                assert type(observation_data) is list
            except KeyError:
                log.warning("No observation for this visit")
            except AssertionError:
                log.error("Observation node is not a list")
                raise
            visit_uuid = uuid.uuid4()
            visit_dict_to_post = {
                "uuid_base_visit": visit_uuid,
                "id_module": gn_module.id_module,
                "data": {},
            }
            observers_list = []
            for key, val in flatten_data.items():
                odk_column_name = key.split("/")[-1]
                # specifig comment column
                if odk_column_name == module_config["VISIT"].get("comments"):
                    visit_dict_to_post["comments"] = val
                # specific media column
                if odk_column_name == module_config["VISIT"].get("media"):
                    visit_media_name = val
                if odk_column_name in visit_generic_column:
                    visit_dict_to_post[odk_column_name] = val
                # specific observers repeat
                if odk_column_name == module_config["VISIT"].get("observers_repeat"):
                    for role in val:
                        observers_list.append(
                            int(role[module_config["VISIT"].get("id_observer")])
                        )
                elif odk_column_name in visit_specific_column:
                    odk_field = odk_form_schema.get_field_info(odk_column_name)
                    if odk_field["selectMultiple"]:
                        if val:
                            # HACK -> convert mutliSelect in list and replace _ by espace
                            val = [v.replace("_", " ") for v in val.split(" ")]
                    visit_dict_to_post["data"][odk_column_name] = val

            #### temp
            # visit_dict_to_post["id_dataset"] = 9744
            ### fin temp
            print("#############", visit_dict_to_post)
            print("OBSERVERS", observers_list)
            visit = TMonitoringVisits(**visit_dict_to_post)
            visit.observers = (
                DB.session.query(User)
                .filter(User.id_role.in_(tuple(observers_list)))
                .all()
            )
            # get_and_post_medium(
            #     project_id=project_id,
            #     form_id=form_id,
            #     uuid_sub=flatten_obs("meta/instanceID").split(":")[1],
            #     filename=visit_media_name,
            #     monitoring_table="t_base_visits",
            #     uuid_gn_object=gn_uuid,
            # )
            # # pp.pprint(sub)

            obs_media_name = None
            for obs in observation_data:
                # print("############ OBS", obs)
                observation_dict_to_post = {
                    "data": {},
                }
                flatten_obs = flatdict.FlatDict(obs, delimiter="/")
                for key, val in flatten_obs.items():
                    odk_column_name = key.split("/")[-1]
                    # specifig comment column
                    if odk_column_name == module_config["OBSERVATION"].get("comments"):
                        observation_dict_to_post["comments"] = val
                    # specific media column
                    if odk_column_name == module_config["OBSERVATION"].get("media"):
                        obs_media_name = val
                    if odk_column_name in observation_generic_column:
                        observation_dict_to_post[odk_column_name] = val
                    elif odk_column_name in observation_specific_column:
                        odk_field = odk_form_schema.get_field_info(odk_column_name)
                        if odk_field["selectMultiple"]:
                            if val:
                                # HACK -> convert mutliSelect in list and replace _ by espace
                                val = [v.replace("_", " ") for v in val.split(" ")]
                        observation_dict_to_post["data"][odk_column_name] = val
                observation = TMonitoringObservations(**observation_dict_to_post)
                visit.observations.append(observation)
            DB.session.add(visit)
            print(visit)
            try:
                DB.session.commit()
            except SQLAlchemyError as e:
                log.error("Error while posting data")
                log.error(str(e))
                send_mail(
                    config["gn_odk"]["email_for_error"],
                    subject="Synchronisation ODK error",
                    msg_html=str(e),
                )
                DB.session.rollback()


@click.command()
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
@click.option('--skip_taxons', is_flag=True, help="Skip taxon sync.")
@click.option('--skip_observers', is_flag=True, help="Skip observers sync.")
@click.option('--skip_jdd', is_flag=True, help="Skip jdd sync.")
@click.option('--skip_sites', is_flag=True, help="Skip sites sync.")
@click.option('--skip_nomenclatures', is_flag=True, help="Skip nomenclatures sync.")
def upgrade_odk_form(
        module_code,
        project_id,
        form_id,
        skip_taxons,
        skip_observers,
        skip_jdd,
        skip_sites,
        skip_nomenclatures
    ):
    log.info(f"--- Start upgrade form for module {module_code} ---")

    app = create_app()

    with app.app_context() as app_ctx:
        # Get Module
        module = get_modules_info(module_code=module_code)
        # Get gn2 attachments data
        files = get_gn2_attachments_data(
            module=module,
            skip_taxons=skip_taxons,
            skip_observers=skip_observers,
            skip_jdd=skip_jdd,
            skip_sites=skip_sites,
            skip_nomenclatures=skip_nomenclatures
        )
        # Update form
        update_form_attachment(
            project_id=project_id,
            xml_form_id=form_id,
            files=files
        )
    log.info(f"--- Done ---")
