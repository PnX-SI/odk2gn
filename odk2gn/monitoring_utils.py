import logging
import uuid
import flatdict
import csv


from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
)
from pypnusershub.db.models import User

from geonature.utils.env import DB

from odk2gn.gn2_utils import format_jdd_list

from gn_module_monitoring.monitoring.models import TMonitoringModules

log = logging.getLogger("app")


def parse_and_create_visit(
    flatten_sub, module_parser_config, monitoring_config, gn_module, odk_form_schema
):
    """
    Parse and create a TMonitoringVisits object from a odk submission
    Return a TMonitoringVisits object

    :param sub: a odk submission with flatten keys
    :type sub: dict

    :param module_parser:_config the odk_gn parser configuration for the current module
    :type module_parser_config: dict

    :param monitoring_config: the monitoring configuration (return by get_config func of gn_module_monitoring func)
    :type monitoring_config: dict

    :param gn_module: the gn_module object
    :type monitoring_config: TMpodulesMonitoring

    :param odk_form_schema: a ODKSchema object describing the ODK form
    :type odk_form_schema: ODKSchema


    """
    visit_generic_column = monitoring_config["visit"]["generic"]
    visit_specific_column = monitoring_config["visit"]["specific"]
    # get uuid from the submission and use it has visit UUID
    visit_uuid = flatten_sub["__id"].split(":")[-1]
    # DB.session.query(TMonitoringVisits).filter_by(uuid_base_visit=visit_uuid).exitst()
    visit_dict_to_post = {
        "uuid_base_visit": visit_uuid,
        "id_module": gn_module.id_module,
        "data": {},
    }
    observers_list = []
    for key, val in flatten_sub.items():
        # print(str(key) + ' : ' + str(val) + ', ' )
        odk_column_name = key.split("/")[-1]
        # specifig comment column
        if odk_column_name == module_parser_config["VISIT"].get("comments"):
            visit_dict_to_post["comments"] = val
        # specific media column
        if odk_column_name == module_parser_config["VISIT"].get("media"):
            visit_media_name = val
        # specific observers repeat
        if odk_column_name == module_parser_config["VISIT"].get("observers_repeat"):
            for role in val:
                observers_list.append(int(role[module_parser_config["VISIT"].get("id_observer")]))
        # print("generic", visit_generic_column)
        if odk_column_name in visit_generic_column.keys():
            # get val or the default value define in gn_monitoring json
            visit_dict_to_post[odk_column_name] = val or visit_generic_column[odk_column_name].get(
                "value"
            )

        elif odk_column_name in visit_specific_column.keys():
            odk_field = odk_form_schema.get_field_info(odk_column_name)
            if odk_field["selectMultiple"]:
                if val:
                    # HACK -> convert mutliSelect in list and replace _ by espace
                    val = [v.replace("_", " ") for v in val.split(" ")]
            visit_dict_to_post["data"][odk_column_name] = val or visit_specific_column[
                odk_column_name
            ].get("value")

    if visit_dict_to_post["id_dataset"] == None:
        jdds = format_jdd_list(gn_module.datasets)
        if len(jdds) == 1:
            val = jdds[0][0]
            visit_dict_to_post["id_dataset"] = val
        else:
            raise Exception("Only one dataset should be passed this way.")

    visit = TMonitoringVisits(**visit_dict_to_post)
    visit.observers = DB.session.query(User).filter(User.id_role.in_(tuple(observers_list))).all()
    specific_column_posted = visit_dict_to_post["data"].keys()
    missing_visit_cols_from_odk = list(set(visit_specific_column) - set(specific_column_posted))
    if len(missing_visit_cols_from_odk) > 0:
        log.warning(
            "The following specific columns are missing from ODK form :\n-{}".format(
                "\n-".join(missing_visit_cols_from_odk)
            )
        )
    return visit


def parse_and_create_obs(
    flatten_obs, module_parser_config, monitoring_config, odk_form_schema, gn_uuid_obs
):
    """
    Parse and create an TMonitoringObservations object from a odk observation
    Return a TMonitoringObservations object

    :param flatten_obs: a odk submission with flatten keys
    :type flatten_obs: dict

    :param module_parser:_config the odk_gn parser configuration for the current module
    :type module_parser_config: dict

    :param monitoring_config: the monitoring configuration (return by get_config func of gn_module_monitoring func)
    :type monitoring_config: dict


    :param odk_form_schema: a ODKSchema object describing the ODK form
    :type odk_form_schema: ODKSchema
    """
    # TODO : make a class and not get these column a each loop
    observation_generic_column = monitoring_config["observation"]["generic"]
    observation_specific_column = monitoring_config["observation"]["specific"]

    observation_dict_to_post = {
        "uuid_observation": gn_uuid_obs,
        "data": {},
    }

    for key, val in flatten_obs.items():
        odk_column_name = key.split("/")[-1]

        # specifig comment column
        if odk_column_name == module_parser_config["OBSERVATION"].get("comments"):
            observation_dict_to_post["comments"] = val
        # specific media column
        if odk_column_name == module_parser_config["OBSERVATION"].get("media"):
            obs_media_name = val
        if odk_column_name in observation_generic_column.keys():
            observation_dict_to_post[odk_column_name] = val or observation_generic_column[
                odk_column_name
            ].get("value")
        elif odk_column_name in observation_specific_column.keys():
            odk_field = odk_form_schema.get_field_info(odk_column_name)
            column_widget = observation_specific_column[odk_column_name].get("type_widget")
            print(column_widget)
            if odk_field["type"] == "string" and column_widget == "nomenclature":
                org_val = val
                try:
                    val = int(val, 10)
                except ValueError:
                    val = org_val

            # if odk_specific_column['type_widget'] == 'nomenclature' and odk_field['type'] == 'string' :
            if odk_field["selectMultiple"]:
                if val:
                    # HACK -> convert mutliSelect in list and replace _ by espace
                    val = [v.replace("_", " ") for v in val.split(" ")]
            observation_dict_to_post["data"][odk_column_name] = val or observation_specific_column[
                odk_column_name
            ].get("value")
    return TMonitoringObservations(**observation_dict_to_post)
