import logging
import pprint
import flatdict
import uuid

import click


from sqlalchemy.exc import SQLAlchemyError

from geonature.utils.config import config
from geonature.utils.env import DB
from geonature.utils.utilsmails import send_mail


from gn_module_monitoring.config.repositories import get_config

from odk2gn.odk_api import (
    get_submissions,
    update_form_attachment,
    ODKSchema,
    update_review_state,
)
from odk2gn.monitoring.utils import (
    parse_and_create_visit,
    parse_and_create_obs,
    parse_and_create_site,
    get_gn2_attachments_data,
    get_modules_info,
    get_and_post_medium,
)
from odk2gn.commands import synchronize, upgrade_odk_form

from odk2gn.monitoring.config_schema import ProcoleSchema

log = logging.getLogger("app")
log.setLevel(logging.INFO)
pp = pprint.PrettyPrinter(width=41, compact=True)


def synchronize_module(module_code, project_id, form_id):
    # odk_form_schema = ODKSchema(project_id, form_id)
    odk_form_schema = {}
    log.info(f"--- Start synchro for module {module_code} ---")
    module_parser_config = {}
    for module in config["ODK2GN"]["modules"]:
        if module["module_code"] == module_code:
            module_parser_config = module
    if module_parser_config == {}:
        log.warning(
            f"No mapping found for module {module_code} - get the default ODK monitoring template mapping !  "
        )
        module_parser_config["module_code"] = module_code

    module_parser_config = ProcoleSchema().load(module_parser_config)

    gn_module = get_modules_info(module_code)

    monitoring_config = get_config(module_code)
    form_data = get_submissions(project_id, form_id)

    for sub in form_data:
        flatten_data = flatdict.FlatDict(sub, delimiter="/")
        try:
            if sub[module_parser_config.get("create_site")] == "true":
                site = parse_and_create_site(
                    flatten_data,
                    module_parser_config,
                    monitoring_config=monitoring_config,
                    module=gn_module,
                )
                DB.session.add(site)
        except:
            print("Error while creating site")
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
        try:
            if sub[module_parser_config.get("create_site")] == "true":
                site.visits.append(visit)
        except:
            pass
        DB.session.add(visit)
        try:
            DB.session.commit()
            update_review_state(project_id, form_id, sub["__id"], "approved")
        except SQLAlchemyError as e:
            log.error("Error while posting data")
            log.error(str(e))
            send_mail(
                config["ODK2GN"]["email_for_error"],
                subject="Synchronisation ODK error",
                msg_html=str(e),
            )
            update_review_state(project_id, form_id, sub["__id"], "hasIssues")
            DB.session.rollback()
            raise
    log.info(f"--- Finish synchronize for module {module_code} ---")


def upgrade_module(
    module_code,
    project_id,
    form_id,
    skip_taxons=True,
    skip_observers=True,
    skip_jdd=True,
    skip_sites=True,
    skip_sites_groups=True,
    skip_nomenclatures=True,
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
        skip_sites_groups=skip_sites_groups,
        skip_nomenclatures=skip_nomenclatures,
    )
    # Update form
    update_form_attachment(project_id=project_id, xml_form_id=form_id, files=files)
    log.info(f"--- Done ---")


@synchronize.command(name="monitoring")
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def synchronize_monitoring(module_code, project_id, form_id):
    synchronize_module(module_code, project_id, form_id)


@upgrade_odk_form.command(name="monitoring")
@click.argument("module_code")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
@click.option("--skip_taxons", is_flag=True, help="Skip taxon sync.")
@click.option("--skip_observers", is_flag=True, help="Skip observers sync.")
@click.option("--skip_jdd", is_flag=True, help="Skip jdd sync.")
@click.option("--skip_sites", is_flag=True, help="Skip sites sync.")
@click.option("--skip_sites_groups", is_flag=True, help="Skip site groups sync.")
@click.option("--skip_nomenclatures", is_flag=True, help="Skip nomenclatures sync.")
def upgrade_monitoring(
    module_code,
    project_id,
    form_id,
    skip_taxons,
    skip_observers,
    skip_jdd,
    skip_sites,
    skip_sites_groups,
    skip_nomenclatures,
):
    upgrade_module(
        module_code,
        project_id,
        form_id,
        skip_taxons,
        skip_observers,
        skip_jdd,
        skip_sites,
        skip_sites_groups,
        skip_nomenclatures,
    )
