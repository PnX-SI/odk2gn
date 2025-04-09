import logging
import pprint
import flatdict
import uuid

import click


from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from geonature.utils.config import config
from geonature.utils.env import DB
from geonature.utils.utilsmails import send_mail


from gn_module_monitoring.config.repositories import get_config

from odk2gn.odk_api import (
    get_submissions,
    update_form_attachment,
    ODKSchema
)
from odk2gn.gn2_utils import commit_data, flat_and_short_dict
from odk2gn.monitoring.utils import (
    parse_and_create_visit,
    parse_and_create_obs,
    parse_and_create_site,
    get_gn2_attachments_data,
    get_modules_info,
    get_and_post_medium,
    get_digitiser
)

from odk2gn.monitoring.config_schema import ProcoleSchema

log = logging.getLogger("app")
log.setLevel(logging.INFO)
pp = pprint.PrettyPrinter(width=41, compact=True)


def test(obj):
    new_obj = {}
    # if isinstance(obj, dict):
    #     test(obj)
    # if isinstance(obj, list):
    #     return {}
        # for el in obj:
        #     test(el)
    for k, v in obj.items():
        new_key = k.split("/")[-1]
        new_obj[new_key] = v

    return new_obj


def synchronize_module(module_code, project_id, form_id):
    odk_form_schema = ODKSchema(project_id, form_id)
    log.info(f"--- Start synchro for module {module_code} ---")
    try:
        gn_module = get_modules_info(module_code=module_code)
    except NoResultFound:
        return
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
        flatten_data = flat_and_short_dict(sub)
        id_digitiser = get_digitiser(flatten_data, module_parser_config)
        site = parse_and_create_site(
            flatten_data,
            module_parser_config,
            monitoring_config=monitoring_config,
            module=gn_module,
            odk_form_schema=odk_form_schema,
        )
        site.id_digitiser = id_digitiser
        get_and_post_medium(
            project_id=project_id,
            form_id=form_id,
            uuid_sub=flatten_data.get("instanceID"),
            filename=flatten_data.get(module_parser_config["SITE"]["media"]),
            monitoring_table="t_base_sites",
            media_type=module_parser_config["SITE"]["media_type"],
            uuid_gn_object=site.uuid_base_site,
        )
        if site:
            DB.session.add(site)

        visit = parse_and_create_visit(
            flatten_data,
            module_parser_config,
            monitoring_config,
            gn_module,
            odk_form_schema,
        )
        if not visit:
            # S'il n'y a pas de visites
            # Sauvegarde des données et passage à la submission suivante
            log.warning("No visit for this site")
            commit_data(project_id, form_id, sub["__id"])
            continue

        visit.id_digitiser = id_digitiser

        get_and_post_medium(
            project_id=project_id,
            form_id=form_id,
            uuid_sub=flatten_data.get("instanceID"),
            filename=flatten_data.get(module_parser_config["VISIT"]["media"]),
            monitoring_table="t_base_visits",
            media_type=module_parser_config["VISIT"]["media_type"],
            uuid_gn_object=visit.uuid_base_visit,
        )

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
        except Exception as e:
            raise

        for obs in observations_list:
            gn_uuid_obs = uuid.uuid4()
            flatten_obs = flat_and_short_dict(obs)
            observation = parse_and_create_obs(
                flatten_obs,
                module_parser_config,
                monitoring_config,
                odk_form_schema,
                gn_uuid_obs,
            )
            observation.id_digitiser = id_digitiser
            get_and_post_medium(
                project_id=project_id,
                form_id=form_id,
                uuid_sub=flatten_data.get("instanceID"),
                filename=flatten_obs.get(module_parser_config["OBSERVATION"]["media"]),
                monitoring_table="t_observations",
                media_type=module_parser_config["OBSERVATION"]["media_type"],
                uuid_gn_object=gn_uuid_obs,
            )
            visit.observations.append(observation)
        if site and visit:
            site.visits.append(visit)

        if visit:
            DB.session.add(visit)

        commit_data(project_id, form_id, sub["__id"])
    log.info(f"--- Finish synchronize for module {module_code} ---")



def upgrade_module(
    module_code,
    project_id,
    form_id,
    skip_taxons=False,
    skip_observers=False,
    skip_jdd=False,
    skip_sites=False,
    skip_sites_groups=False,
    skip_nomenclatures=False,
):
    log.info(f"--- Start upgrade form for module {module_code} ---")
    try:
        module = get_modules_info(module_code=module_code)
    except NoResultFound:
        return
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
