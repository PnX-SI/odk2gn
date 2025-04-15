import logging
import datetime

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringSitesGroups,
)

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_commons.models import BibTablesLocation, TMedias
from odk2gn.odk_api import get_attachment
from odk2gn.gn2_utils import format_jdd_list, get_observers
from geonature.core.gn_monitoring.models import TBaseSites
from gn_module_monitoring.monitoring.models import TMonitoringModules

log = logging.getLogger("app")

from pypnnomenclature.models import TNomenclatures
from odk2gn.gn2_utils import (
    format_jdd_list,
    get_id_nomenclature_type_site,
    to_wkb,
    get_nomenclature_data,
    get_observer_list,
    get_taxon_list,
    to_csv,
)


def get_site_type_cd_nomenclature(monitoring_config):
    return monitoring_config["site"]["generic"]["id_nomenclature_type_site"]["value"][
        "cd_nomenclature"
    ]


def parse_and_create_site(flatten_sub, module_parser_config, monitoring_config, module):
    site_specific_column = monitoring_config["site"]["specific"]
    # a ne pas être hard codé dans le futur
    cd_nomenclature = get_site_type_cd_nomenclature(monitoring_config)
    id_type = get_id_nomenclature_type_site(cd_nomenclature=cd_nomenclature)
    site_dict_to_post = {
        "id_module": module.id_module,
        "id_nomenclature_type_site": id_type,
        "data": {},
    }

    geom_type = None
    coords = None
    for key, val in flatten_sub.items():
        odk_column_name = key.split("/")[-1]
        id_groupe = None  # pour éviter un try except plus bas
        if module_parser_config["SITE"].get("create_site") == odk_column_name:
            create_site_key = module_parser_config["SITE"].get("create_site")
            if flatten_sub[create_site_key] in ("0", 0, "false", "no", False, None):
                return None
        elif odk_column_name == module_parser_config["SITE"].get("base_site_name"):
            site_dict_to_post["base_site_name"] = val
        elif odk_column_name == module_parser_config["SITE"].get("base_site_description"):
            site_dict_to_post["base_site_description"] = val
        elif odk_column_name == module_parser_config["SITE"].get("first_use_date"):
            # on utilise la valeur de la visite pour éviter d'entrer deux fois la même valeur
            site_dict_to_post["first_use_date"] = datetime.datetime.fromisoformat(val)
        elif odk_column_name == module_parser_config["SITE"].get("id_inventor"):
            # là encore on utilise la valeur de la visite pour éviter la double entrée
            site_dict_to_post["id_inventor"] = int(val[0]["id_role"])
        elif odk_column_name == module_parser_config["SITE"].get("site_group"):
            # transtypage pour la solidité des données
            try:
                id_groupe = int(val)
                site_dict_to_post["id_sites_group"] = id_groupe
            except Exception as e:
                log.error(e)
                pass
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
        elif odk_column_name in site_specific_column.keys():
            site_dict_to_post["data"][odk_column_name] = val
    site = TMonitoringSites(**site_dict_to_post)
    # pour la géométrie on construit un geoJSON et on le transforme
    geom = {"type": geom_type, "coordinates": coords}
    print("????????", geom)
    # format_coords(geom)
    geom = to_wkb(geom)
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
    :type monitoring_config: TModulesMonitoring

    :param odk_form_schema: a ODKSchema object describing the ODK form
    :type odk_form_schema: ODKSchema


    """
    visit_generic_column = monitoring_config["visit"]["generic"]
    visit_specific_column = monitoring_config["visit"]["specific"]
    # get uuid from the submission and use it has visit UUID
    visit_uuid = flatten_sub["__id"].split(":")[-1]
    visit_dict_to_post = {
        "uuid_base_visit": visit_uuid,
        "id_module": gn_module.id_module,
        "data": {},
    }
    observers_list = []
    for key, val in flatten_sub.items():
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
            raise AssertionError("Only one dataset should be passed this way.")
    visit = TMonitoringVisits(**visit_dict_to_post)
    visit.observers = get_observers(observers_list)
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


def get_modules_info(module_code: str):
    try:
        module = TMonitoringModules.query.filter(
            TMonitoringModules.module_code.ilike(module_code)
        ).one()
        return module
    except NoResultFound:
        log.error(f"No GeoNature module found for {module_code}")
        raise


def get_site_groups_list(id_module: int):
    """Return dict of TMonitoringSitesGroups

    :param id_module: Identifier of the module
    :type id_module : int"""

    data = (
        DB.session.query(TMonitoringSitesGroups)
        .order_by(TMonitoringSitesGroups.sites_group_name)
        .filter_by(id_module=id_module)
        .all()
    )

    return [group.as_dict() for group in data]


def get_gn2_attachments_data(
    module: TMonitoringModules,
    skip_taxons: bool = False,
    skip_observers: bool = False,
    skip_jdd: bool = False,
    skip_sites: bool = False,
    skip_nomenclatures: bool = False,
    skip_sites_groups: bool = False,
):
    files = {}
    # Taxon
    if not skip_taxons:
        data = get_taxon_list(module.id_list_taxonomy)
        files["gn_taxons.csv"] = to_csv(header=("cd_nom", "nom_complet", "nom_vern"), data=data)
    # Observers
    if not skip_observers:
        data = get_observer_list(module.id_list_observer)
        files["gn_observateurs.csv"] = to_csv(header=("id_role", "nom_complet"), data=data)
    # JDD
    if not skip_jdd:
        data = format_jdd_list(module.datasets)
        files["gn_jdds.csv"] = to_csv(header=("id_dataset", "dataset_name"), data=data)

    # Sites
    if not skip_sites:
        data = get_site_list(module.id_module)
        files["gn_sites.csv"] = to_csv(
            header=("id_base_site", "base_site_name", "geometry"), data=data
        )

    if not skip_sites_groups:
        data = get_site_groups_list(module.id_module)
        files["gn_groupes.csv"] = to_csv(header=("id_sites_group", "sites_group_name"), data=data)

    # Nomenclature
    if not skip_nomenclatures:
        n_fields = []
        for niveau in ["site", "visit", "observation"]:
            n_fields = n_fields + get_nomenclatures_fields(
                module_code=module.module_code, niveau=niveau
            )

        nomenclatures = get_nomenclature_data(n_fields)
        files["gn_nomenclatures.csv"] = to_csv(
            header=("mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"),
            data=nomenclatures,
        )

    return files


def get_site_list(id_module: int):
    """Return tuple of TBase site for module

    :param id_module: Identifiant du module
    :type id_module: int
    """
    data = (
        DB.session.query(
            TBaseSites.id_base_site,
            TBaseSites.base_site_name,
            func.concat(
                func.st_y(func.st_centroid(TBaseSites.geom)),
                " ",
                func.st_x(func.st_centroid(TBaseSites.geom)),
            ),
        )
        .order_by(TBaseSites.base_site_name)
        .filter(TMonitoringSites.id_base_site == TBaseSites.id_base_site)
        .filter(TMonitoringSites.id_module == id_module)
        .all()
    )
    res = []
    for d in data:
        res.append({"id_base_site": d[0], "base_site_name": d[1], "geometry": d[2]})
    return res


def get_site_groups_list(id_module: int):
    """Return dict of TMonitoringSitesGroups

    :param id_module: Identifier of the module
    :type id_module : int"""

    data = (
        DB.session.query(TMonitoringSitesGroups)
        .order_by(TMonitoringSitesGroups.sites_group_name)
        .filter_by(id_module=id_module)
        .all()
    )

    return [group.as_dict() for group in data]


def get_nomenclatures_fields(module_code: str, niveau: str):
    config = get_config(module_code)
    fields = dict(
        config[niveau].get("specific", []),
        **config[niveau].get("generic", []),
    )
    nomenclatures_fields = []
    for name in fields:
        form = fields[name]
        type_util = form.get("type_util")
        type_widget = form.get("type_widget")

        # composant nomenclature
        if type_widget == "nomenclature":
            if form["code_nomenclature_type"]:
                nomenclatures_fields.append(
                    {
                        "code_nomenclature_type": form["code_nomenclature_type"],
                        "cd_nomenclatures": form.get("cd_nomenclatures", None),
                    }
                )

        # composant datalist
        if type_widget == "datalist":
            if type_util == "nomenclature":
                code_nomenclature_type = form.get("api").split("/")[-1]
                nomenclatures_fields.append(
                    {
                        "code_nomenclature_type": code_nomenclature_type,
                        "regne": form.get("params", {}).get("regne"),
                        "group2_inpn": form.get("params", {}).get("group2_inpn"),
                    }
                )
    return nomenclatures_fields


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
        try:
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
        except:
            pass
