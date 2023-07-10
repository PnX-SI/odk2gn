import logging
import uuid
import flatdict
import csv
import datetime
from shapely.geometry import Polygon, Point, LineString


from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringSitesGroups,
)
from pypnusershub.db.models import User

from geonature.utils.env import DB

from odk2gn.gn2_utils import format_jdd_list
from geonature.core.gn_monitoring.models import TBaseSites
from gn_module_monitoring.monitoring.models import TMonitoringModules

log = logging.getLogger("app")

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from odk2gn.gn2_utils import format_jdd_list
from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import (
    to_wkt,
    format_coords,
)


def parse_and_create_site(flatten_sub, module_parser_config, module):
    # a ne pas être hard codé dans le futur
    if module.module_code == "STOM":
        cd_nom = "STOM"
    if module.module_code == "suivi_nardaie":
        cd_nom = "SUIVI_NARDAIE"
    if module.module_code == "chiro":
        cd_nom = "CHI"
    id_type = (
        TNomenclatures.query.join(TNomenclatures.nomenclature_type, aliased=True)
        .filter_by(mnemonique="TYPE_SITE")
        .filter(TNomenclatures.cd_nomenclature == cd_nom)
        .one()
    ).id_nomenclature

    site_dict_to_post = {
        "id_module": module.id_module,
        "id_nomenclature_type_site": id_type,
        "data": {},
    }
    #
    for key, val in flatten_sub.items():
        odk_column_name = key.split("/")[-1]
        id_groupe = None  # pour éviter un try except plus bas
        if odk_column_name == module_parser_config["SITE"].get("base_site_name"):
            site_dict_to_post["base_site_name"] = val
        elif odk_column_name == module_parser_config["SITE"].get("base_site_description"):
            site_dict_to_post["base_site_description"] = val
        elif odk_column_name == module_parser_config["SITE"].get("first_use_date"):
            # on utilise la valeur de la visite pour éviter d'entrer deux fois la même valeur
            site_dict_to_post["first_use_date"] = datetime.datetime.fromisoformat(val)
        elif odk_column_name == module_parser_config["SITE"].get("id_inventor"):
            # là encore on utilise la valeur de la visite pour éviter la double entrée
            site_dict_to_post["id_inventor"] = int(val[0]["id_role"])
        elif odk_column_name == "site_group":
            # transtypage pour la solidité des données
            id_groupe = int(val)
            site_dict_to_post["id_sites_group"] = id_groupe

        # données géométriques
        # type, coordinates et accuracy sont des noms de variables qui seront toujours présents dans une donnée géométrique d'ODK, ils sont déjà génériques
        elif odk_column_name == "type" and module_parser_config["SITE"].get("geom") in key:
            geom_type = val
        elif odk_column_name == "coordinates" and module_parser_config["SITE"].get("geom") in key:
            coords = val
        # la précision n'est pas relevée en BDD, donc on sépare son cas pour ne rien faire avec
        elif odk_column_name == "accuracy" and module_parser_config["SITE"].get("geom") in key:
            pass
        # tous les spécificités d'un site d'un module
        # changer site_creation pour le nom du group du XLSFORM où ces données figurent
        # elif "site_creation" in key:
        elif module_parser_config["SITE"].get("data") in key:
            site_dict_to_post["data"][odk_column_name] = val
    site = TMonitoringSites(**site_dict_to_post)
    # pour la géométrie on construit un geoJSON et on le transforme
    geom = {"type": geom_type, "coordinates": coords}
    format_coords(geom)
    geom = to_wkt(geom)
    site.geom = geom

    # traitements des relations BDD
    site.modules.append(module)
    module.sites.append(site)  # redondance?

    # traitement de ce qui peut éventuellement être de valeur nulle
    if site.data == {}:
        site.data = None
    if id_groupe is not None:
        groupe = TMonitoringSitesGroups.query.filter_by(id_sites_group=id_groupe).one()
        groupe.sites.append(site)
    return site


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
            val = jdds[0]["id_dataset"]
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
            if odk_field["type"] == "string" and column_widget == "nomenclature":
                org_val = val
                try:
                    val = int(val, 10)
                except:
                    val = org_val

            # if odk_specific_column['type_widget'] == 'nomenclature' and odk_field['type'] == 'string' :
            if odk_field["selectMultiple"]:
                if val:
                    # HACK -> convert mutliSelect in list and replace _ by espace
                    val = [v.replace("_", " ") for v in val.split(" ")]
            observation_dict_to_post["data"][odk_column_name] = val or observation_specific_column[
                odk_column_name
            ].get("value")
    obs = TMonitoringObservations(**observation_dict_to_post)
    return obs


{
    "__id": "uuid:8fd82b0f-bde1-4a00-a71f-13aafa6d245c",
    "date_time": "2023-07-05T14:19:38.437+02:00",
    "presentation/presentation": None,
    "create_site": "true",
    "site_creation/site_group": "1",
    "site_creation/site_name": "site_0",
    "site_creation/base_site_description": None,
    "site_creation/geom/type": "Point",
    "site_creation/geom/coordinates": [6.053762, 44.578176, 0],
    "site_creation/geom/properties/accuracy": 0,
    "sites/id_base_site": None,
    "visit_1/visit_date_min": "2023-07-05T14:19:38.426+02:00",
    "visit_1/observers@odata.navigationLink": "Submissions('uuid%3A8fd82b0f-bde1-4a00-a71f-13aafa6d245c')/visit_1/observers",
    "visit_1/observers": [
        {"id_role": "3", "__id": "b7caf4fe58522b2ee8d9774c70a17bfaf316744b"},
        {"id_role": "4", "__id": "8b3455d193e0d481761598ecdcb40c79e352bb05"},
    ],
    "visit_2/id_dataset": None,
    "visit_2/debutant": "false",
    "visit_2/heure": "14:19:38.433+02:00",
    "visit_2/nuages": None,
    "visit_2/pluie": None,
    "visit_2/vent": None,
    "visit_2/visi": None,
    "visit_2/deneigement": None,
    "visit_2/paturage": None,
    "visit_2/comments_visit": None,
    "visit_habitat/habitat_desc": "false",
    "habitat/elem_paysager": None,
    "habitat/comment_paysage": None,
    "Habitat2/elem_habitat": None,
    "habitat_percent/roche": None,
    "habitat_percent/sol_nu": None,
    "habitat_percent/herb": None,
    "habitat_percent/arb_inf_30cm": None,
    "habitat_percent/arb_inf_1m": None,
    "habitat_percent/arb_1_4m": None,
    "habitat_percent/arb_sup_4m": None,
    "habitat_percent/habitat_roche": None,
    "habitat_percent/habitat_sol_nu": None,
    "habitat_percent/habitat_herb": None,
    "habitat_percent/habitat_arb_inf_30cm": None,
    "habitat_percent/habitat_arb_inf_1m": None,
    "habitat_percent/habitat_arb_1_4m": None,
    "habitat_percent/habitat_arb_sup_4m": None,
    "habitat_percent/habitat_couverture": None,
    "habitat_percent/habitat_recap": None,
    "habitat_percent/habitat_percent_trigger": None,
    "meta/instanceID": "uuid:8fd82b0f-bde1-4a00-a71f-13aafa6d245c",
    "__system/submissionDate": "2023-07-05T12:18:39.424Z",
    "__system/updatedAt": None,
    "__system/submitterId": "98",
    "__system/submitterName": "Xavier Davis",
    "__system/attachmentsPresent": 0,
    "__system/attachmentsExpected": 0,
    "__system/status": None,
    "__system/reviewState": None,
    "__system/deviceId": None,
    "__system/edits": 0,
    "__system/formVersion": "7",
    "observations@odata.navigationLink": "Submissions('uuid%3A8fd82b0f-bde1-4a00-a71f-13aafa6d245c')/observations",
    "observations": [
        {
            "sp_choice": {"cd_nom": None},
            "sp_label": None,
            "sp_nbre": {
                "sp_note": None,
                "nb_0_5": None,
                "nb_5_10": None,
                "nb_10_15": None,
                "nb_hors_proto": None,
                "presence_juvenile": "false",
                "comments_observation": None,
            },
            "__id": "9eee80c31dc0d1d61c4818da4621d9d0bb0988b4",
        }
    ],
}
