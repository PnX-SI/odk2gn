import logging
import datetime

from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound

from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
    TMonitoringSitesGroups,
)

from geonature.utils.env import DB, BACKEND_DIR
from geonature.core.gn_commons.models import BibTablesLocation, TMedias, TModules
from geonature.core.gn_monitoring.models import TBaseSites, BibTypeSite
from gn_module_monitoring.monitoring.models import TMonitoringModules, cor_module_type
from pypnnomenclature.models import TNomenclatures
from pypnusershub.db.models import User

from odk2gn.odk_api import get_attachment
from odk2gn.gn2_utils import (
    format_jdd_list,
    to_wkb,
    get_nomenclature_data,
    get_observer_list,
    get_taxon_list,
    to_csv,
    get_observers
)

log = logging.getLogger("app")

def additional_data_is_multiple_nomenclature(monitoring_config, field_name):
    """
    Cas des champs à choix multiple de type nomenclature
    ODK stocke les valeurs des choix multiples séparées par un espace
        dans le cas des nomenclatures la valeur retournée est une suite d'id
            séparés par un espace.

    Return True quand le champ est de type nomenclature et à choix multiple
    """
    if field_name in monitoring_config["specific"]:
        field_config = monitoring_config["specific"][field_name]
        if (
            field_config.get("type_util", None) == "nomenclature"
            and field_config.get("multiple", None) == True
        ):
            return True
        else:
            return False
    else:
        return False


def additional_data_is_nomenclature(monitoring_config, field_name):
    """
    Cas des champs à choix multiple de type nomenclature
    ODK stocke les valeurs des choix multiples séparées par un espace
        dans le cas des nomenclatures la valeur retournée est une suite d'id
            séparés par un espace.

    Return True quand le champ est de type nomenclature et à choix multiple
    """
    if field_name in monitoring_config["specific"]:
        field_config = monitoring_config["specific"][field_name]
        if field_config.get("type_util", None) == "nomenclature":
            return True
        else:
            return False
    else:
        return False


def process_additional_data(monitoring_config, odk_form_schema, field_name, val):
    odk_field = odk_form_schema.get_field_info(field_name)

    if additional_data_is_multiple_nomenclature(monitoring_config, field_name) and val:
        # Cas particulier des valeurs multiples pour les nomenclatures
        return [int(v) for v in val.split(" ") if v]
    elif additional_data_is_nomenclature(monitoring_config, field_name) and val:
        # Cas particulier des valeurs multiples pour les nomenclatures
        return int(val)
    elif odk_field["selectMultiple"]:
        if val:
            # HACK -> convert mutliSelect in list and replace _ by espace
            return [v.replace("_", " ") for v in val.split(" ")]
    else:
        return val


def get_digitiser(flatten_sub, module_parser_config):
    for key, val in flatten_sub.items():
        odk_column_name = key.split("/")[-1]
        # specifig digitiser column
        if odk_column_name == module_parser_config.get("id_digitiser"):
            return int(val)


def get_observers(observers_list):
    obss = DB.session.query(User).filter(User.id_role.in_(tuple(observers_list))).all()
    return obss



def parse_and_create_site(
    flatten_sub, module_parser_config, monitoring_config, module, odk_form_schema
):
    # Test de création du site
    # S'il y a un champ create_site dans le formulaire
    #   et qu'il  est  renseigné de façon négative
    if module_parser_config.get("create_site") in flatten_sub.keys():
        create_site_key = module_parser_config.get("create_site")
        if flatten_sub[create_site_key] in ("0", 0, "false", "no", False, None):
            return None

    id_type = None
    site_dict_to_post = {
        "data": {},
    }
    site_specific_fields = monitoring_config["site"]["specific"]
    types_site = []
    for key, val in flatten_sub.items():
        id_groupe = None  # pour éviter un try except plus bas
        if key == module_parser_config["SITE"].get("types_site"):
            types_site = [int(v) for v in val.split(" ") if v]
        if key == module_parser_config["SITE"].get("base_site_name"):
            site_dict_to_post["base_site_name"] = val
        elif key == module_parser_config["SITE"].get("base_site_description"):
            site_dict_to_post["base_site_description"] = val
        elif key == module_parser_config["SITE"].get("first_use_date"):
            # on utilise la valeur de la visite pour éviter d'entrer deux fois la même valeur
            site_dict_to_post["first_use_date"] = datetime.datetime.fromisoformat(val)
        elif key == module_parser_config["SITE"].get("id_inventor"):
            # là encore on utilise la valeur de la visite pour éviter la double entrée
            if isinstance(val[0], int):
                site_dict_to_post["id_inventor"] = val[0]
            elif "id_role" in val[0]:
                site_dict_to_post["id_inventor"] = int(val[0]["id_role"])
            else:
                site_dict_to_post["id_inventor"] = val
        elif key == module_parser_config["SITE"].get("site_group"):
            # transtypage pour la solidité des données
            id_groupe = int(val)
            site_dict_to_post["id_sites_group"] = id_groupe

        # données géométriques
        # type, coordinates et accuracy sont des noms de variables qui seront toujours présents dans une donnée géométrique d'ODK, ils sont déjà génériques
        elif key == "type":
            geom_type = val
        elif key == "coordinates":
            coords = val
        # Champs additionnels
        elif key in site_specific_fields.keys():
            site_dict_to_post["data"][key] = process_additional_data(
                monitoring_config["site"], odk_form_schema, key, val
            )

    site = TMonitoringSites(**site_dict_to_post)
    # pour la géométrie on construit un geoJSON et on le transforme
    geom = {"type": geom_type, "coordinates": coords}
    # format_coords(geom)
    geom = to_wkb(geom)
    site.geom = geom

    # Récupération des types de sites
    for id_type in types_site:
        ts = DB.session.scalar(
            select(BibTypeSite).filter(BibTypeSite.id_nomenclature_type_site == id_type).limit(1)
        )
        site.types_site.append(ts)


    if id_groupe is not None:
        groupe = TMonitoringSitesGroups.query.filter_by(id_sites_group=id_groupe).one()
        groupe.sites.append(site)

    return site


def parse_and_create_visit(
    flatten_sub, module_parser_config, monitoring_config, gn_module, odk_form_schema
):
    """
    Parse and create a TMonitoringVisits object from a odk submission
    Return a TMonitorinODKSchemagVisits object

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
    if not "visit" in monitoring_config:
        # si pas de visite pour le module
        return None

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

    # Test de création de la visite
    # S'il y a un champ create_visit dans le formulaire
    #   et qu'il n'est pas renseigné de façon négative
    if module_parser_config.get("create_visit") in flatten_sub.keys():
        create_site_key = module_parser_config.get("create_visit")
        if flatten_sub[create_site_key] in ("0", 0, "false", "no", False, None):
            return None

    for key, val in flatten_sub.items():
        # specifig comment column
        if key == module_parser_config["VISIT"].get("comments"):
            visit_dict_to_post["comments"] = val
        # specific observers repeat
        if key == module_parser_config["VISIT"].get("observers_repeat"):
            if isinstance(val, (tuple, list, set)):
                for role in val:
                    observers_list.append(
                        int(role[module_parser_config["VISIT"].get("id_observer")])
                    )
            else:
                observers_list.append(val)
        if key in visit_generic_column.keys():
            # get val or the default value define in gn_monitoring json
            visit_dict_to_post[key] = val or visit_generic_column[key].get(
                "value"
            )
        elif key in visit_specific_column.keys():
            process_value = process_additional_data(
                monitoring_config["visit"], odk_form_schema, key, val
            )
            visit_dict_to_post["data"][key] = process_value or visit_specific_column[
                key
            ].get("value")

    if visit_dict_to_post.get("id_dataset", None) == None:
        jdds = format_jdd_list(gn_module.datasets)
        if len(jdds) == 1:
            val = jdds[0]["id_dataset"]
            visit_dict_to_post["id_dataset"] = val
        else:
            raise AssertionError(
                "Dataset cannot be None or multiple"
                )
    visit = TMonitoringVisits(**visit_dict_to_post)
    if not observers_list:
        log.warning("No observers for this visit")
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
        # specifig comment column
        if key == module_parser_config["OBSERVATION"].get("comments"):
            observation_dict_to_post["comments"] = val
        if key in observation_generic_column.keys():
            observation_dict_to_post[key] = val or observation_generic_column[
                key
            ].get("value")
        elif key in observation_specific_column.keys():
            process_value = process_additional_data(
                monitoring_config["observation"], odk_form_schema, key, val
            )
            observation_dict_to_post["data"][key] = (
                process_value or observation_specific_column[key].get("value")
            )
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
        types_site = get_type_site_nomenclature_list(module.id_module)

        nomenclatures = get_nomenclature_data(n_fields)
        nomenclatures = nomenclatures + types_site
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

    # Available type
    type_list = DB.session.scalar(
        select(TMonitoringModules).filter(TMonitoringModules.id_module == id_module).limit(1)
    )
    query = select(
        TBaseSites.id_base_site,
        TBaseSites.base_site_name,
        func.concat(
            func.st_y(func.st_centroid(TBaseSites.geom)),
            " ",
            func.st_x(func.st_centroid(TBaseSites.geom)),
        ),
    ).filter(
        TMonitoringSites.types_site.any(
            BibTypeSite.id_nomenclature_type_site.in_(
                [t.id_nomenclature_type_site for t in type_list.types_site]
            )
        )
    )
    data = DB.session.execute(query.order_by(TBaseSites.base_site_name)).all()
    res = []
    for d in data:
        res.append({"id_base_site": d[0], "base_site_name": d[1], "geometry": d[2]})
    return res


def get_site_groups_list(id_module: int):
    """Return dict of TMonitoringSitesGroups

    :param id_module: Identifier of the module
    :type id_module : int"""

    data = DB.session.scalars(
        select(TMonitoringSitesGroups)
        .filter(TMonitoringSitesGroups.modules.any(TModules.id_module == id_module))
        .order_by(TMonitoringSitesGroups.sites_group_name)
    ).all()

    return [group.as_dict() for group in data]


def get_nomenclatures_fields(module_code: str, niveau: str):
    config = get_config(module_code)
    fields = dict(
        config.get(niveau, {}).get("specific", {}),
        **config.get(niveau, {}).get("generic", {}),
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
    img = get_attachment(project_id, form_id, uuid_sub, filename)
    medias_name = f"{uuid_sub}_{filename}"
    if img:
        uuid_sub = uuid_sub.split(":")[1]
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
            "media_path": f"{table_location.id_table_location}/{medias_name}",
            "uuid_attached_row": uuid_gn_object,
            "id_table_location": table_location.id_table_location,
            "id_nomenclature_media_type": media_type.id_nomenclature,
        }

        media = TMedias(**media)
        DB.session.add(media)
        DB.session.commit()

        media_dir = (
            BACKEND_DIR / "media" / "attachments" / str(table_location.id_table_location)
        )
        media_dir.mkdir(parents=True, exist_ok=True)
        with open(
            media_dir / medias_name,
            "wb",
        ) as out_file:
            out_file.write(img)



def get_type_site_nomenclature_list(
    id_module: int,
):

    q = (
        select(TNomenclatures)
        .join(
            cor_module_type,
            cor_module_type.c.id_type_site == TNomenclatures.id_nomenclature,
        )
        .where(cor_module_type.c.id_module == id_module)
    )
    tab = []
    data = DB.session.scalars(q).all()
    for d in data:
        dict = d.as_dict(relationships=["nomenclature_type"])
        res = {
            "mnemonique": dict["nomenclature_type"]["mnemonique"],
            "id_nomenclature": dict["id_nomenclature"],
            "cd_nomenclature": dict["cd_nomenclature"],
            "label_default": dict["label_default"],
        }
        tab.append(res)
    return tab
