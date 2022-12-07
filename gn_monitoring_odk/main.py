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
    TMonitoringObservations
)

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
            # flatten_dict = NestedDictAccessor(sub)
            flatten_data = flatdict.FlatDict(sub, delimiter="/")
            observation_data = []
            try:
                observation_data = flatten_data.pop(config["OBSERVATION"]["path"])
                assert type(observation_data) is list
            except KeyError:
                log.warning("No observation for this visit")
            except AssertionError:
                log.error("Observation node is not a list")
                raise
            visit_dict_to_post = {"data": {}}
            for key, val in flatten_data.items():
                odk_column_name = key.split("/")[-1]
                if odk_column_name in visit_default_column:
                    visit_dict_to_post[odk_column_name] = val
                elif odk_column_name in visit_json_columns:
                    odk_field = odk_form_schema.get_field_info(odk_column_name)
                    if odk_field["selectMultiple"]:
                        if val:
                            # HACK -> convert mutliSelect in list and replace _ by espace
                            val = [v.replace("_", " ") for v in val.split(" ")]
                    visit_dict_to_post["data"][odk_column_name] = val
            print("VISIT TO POST")
            print(visit_dict_to_post)

            observation_dict_to_post = {"data": {}}
            for obs in observation_data:
                flatten_obs = flatdict.FlatDict(obs, delimiter="/")
                for key, val in flatten_obs.items():
                    odk_column_name = key.split("/")[-1]
                    if odk_column_name in observation_default_column:
                        observation_dict_to_post[odk_column_name] = val
                    elif odk_column_name in observation_json_columns:
                        odk_field = odk_form_schema.get_field_info(odk_column_name)
                        if odk_field["selectMultiple"]:
                            if val:
                                # HACK -> convert mutliSelect in list and replace _ by espace
                                val = [v.replace("_", " ") for v in val.split(" ")]
                        observation_dict_to_post["data"][odk_column_name] = val
            print("OBS TO POST")
            print(observation_dict_to_post)

            # # pp.pprint(sub)

            # id_dataset = (
            #     flatten_data.get_nested(config["VISIT"]["id_dataset"])
            #     or config["VISIT"]["default_id_dataset"]
            # )
            # observers_str = flatten_data.get_nested(config["VISIT"]["observers"])
            # observers_list = []
            # observers_list = DB.session.query(User).filter(
            #     User.id_role.in_(observers_str.split(" "))
            # )

            # visit_json_dict = {}
            # for path in config["VISIT"]["data"]:
            #     visit_json_dict[path.split("/")[-1]] = flatten_data.get_nested(path)
            # gn_uuid = uuid.uuid4()
            # visite = TMonitoringVisits(
            #     uuid_base_visit=gn_uuid,
            #     id_base_site=1,
            #     id_dataset=id_dataset,
            #     id_module=gn_module.id_module,
            #     visit_date_min=flatten_dict.get_nested(config["VISIT"]["date_min"]),
            #     visit_date_max=flatten_dict.get_nested(config["VISIT"]["date_min"]),
            #     comments=flatten_dict.get_nested(config["VISIT"]["comments"]),
            #     data=visit_json_dict,
            #     observers=observers_list,
            # )
            # get_and_post_medium(
            #     project_id=project_id,
            #     form_id=form_id,
            #     uuid_sub=sub.get_nested("meta.instanceID").split(":")[1],
            #     filename=sub.get_nested(config["VISIT"]["media_name"]),
            #     monitoring_table="t_base_visits",
            #     uuid_gn_object=gn_uuid,
            # )
            # observations = flatten_dict.get_nested(config["VISIT"]["observations"])
            # for obs in observations:
            #     obs_json_dict = {}
            #     for path in config["OBSERVATION"]["data"]:
            #         obs_json_dict[path.split("/")[-1]] = obs.get_nested(path)
            #     uuid_obs = uuid.uuid4()
            #     observation = TMonitoringObservations(
            #         uuid_observation=uuid_obs,
            #         cd_nom=obs.get_nested(config["OBSERVATION"]["cd_nom"]),
            #         comments=obs.get_nested(config["OBSERVATION"]["comments"]),
            #         data=obs_json_dict,
            #     )
            #     get_and_post_medium(
            #         project_id=project_id,
            #         form_id=form_id,
            #         uuid_sub=sub.get_nested("meta.instanceID").split(":")[1],
            #         filename=sub.get_nested(config["OBSERVATION"]["media_name"]),
            #         monitoring_table="t_observations",
            #         uuid_gn_object=uuid_obs,
            #     )

            #     visite.observations.append(observation)

            # DB.session.add(visite)

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
        files = get_gn2_attachments_data(
            module=module,
            id_nomeclature_type=[]
        )
        # Update form
        update_form_attachment(
            project_id=project_id,
            xml_form_id=form_id,
            files=files
        )
    log.info(f"--- Done ---")
