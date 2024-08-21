import logging
import os
import csv
import json
import geojson
from shapely.geometry import shape, Point, Polygon
from shapely.ops import transform
from geoalchemy2.shape import from_shape

import tempfile
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select, join
from geonature.utils.env import DB
from geonature.core.users.models import VUserslistForallMenu
from geonature.core.gn_meta.models import TDatasets
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_monitoring.models import TBaseSites
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringSitesGroups,
)

from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature

from odk2gn.monitoring_config import get_nomenclatures_fields
from apptax.taxonomie.models import Taxref

log = logging.getLogger("app")


def get_monitoring_modules():
    tab = []
    modules = (TMonitoringModules).query.filter_by(type="monitoring_modules").all()
    for module in modules:
        tab.append(module)
    return tab


def get_module_code(id_module: int):
    module_code = (TModules.query.filter_by(id_module=id_module).one()).module_code
    return module_code


def get_modules_info(module_code: str):
    try:
        module = TMonitoringModules.query.filter(
            TMonitoringModules.module_code.ilike(module_code)
        ).one()
        return module
    except NoResultFound:
        log.error(f"No GeoNature module found for {module_code}")
        raise


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


def get_taxon_list(id_liste: int):
    """Return dict of Taxref

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = (
        DB.session.query(Taxref)
        .order_by(Taxref.nom_complet)
        .filter(Taxref.listes.any(id_liste=id_liste))
        .limit(3000)
    )
    taxons = []
    for tax in data:
        tax = tax.as_dict()
        if tax["nom_vern"] is not None:
            tax["nom_complet"] = tax["nom_complet"] + " - " + tax["nom_vern"]
        taxons.append(tax)
    return taxons


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


def get_observer_list(id_liste: int):
    """Return tuple of Observers for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = (
        DB.session.query(VUserslistForallMenu)
        .order_by(VUserslistForallMenu.nom_complet)
        .filter_by(id_menu=id_liste)
        .all()
    )
    return [obs.as_dict() for obs in data]


def format_jdd_list(datasets: list):
    """Return tuple of Dataset

    :param datasets: List of associated dataset
    :type datasets: []
    """
    data = []
    for jdd in datasets:
        data.append({"id_dataset": jdd.id_dataset, "dataset_name": jdd.dataset_name})
    return data


def get_ref_nomenclature_list(
    code_nomenclature_type: str,
    cd_nomenclatures: list = None,
    regne: str = None,
    group2_inpn: str = None,
):
    q = TNomenclatures.query.join(TNomenclatures.nomenclature_type, aliased=True).filter_by(
        mnemonique=code_nomenclature_type
    )
    if cd_nomenclatures:
        q = q.filter(TNomenclatures.cd_nomenclature.in_(cd_nomenclatures))

    if regne:
        q = q.filter(
            CorTaxrefNomenclature.id_nomenclature == TNomenclatures.id_nomenclature
        ).filter(CorTaxrefNomenclature.regne == regne)
        if group2_inpn:
            q = q.filter(CorTaxrefNomenclature.group2_inpn == group2_inpn)
    tab = []
    data = q.all()
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


def get_nomenclature_data(nomenclatures_fields):
    data = []
    for f in nomenclatures_fields:
        data = data + get_ref_nomenclature_list(**f)

    return data


def get_id_nomenclature_type_site(cd_nomenclature):
    id_nomenclature_type_site = (
        TNomenclatures.query.join(TNomenclatures.nomenclature_type, aliased=True)
        .filter_by(mnemonique="TYPE_SITE")
        .filter(TNomenclatures.cd_nomenclature == cd_nomenclature)
        .one()
    ).id_nomenclature
    return id_nomenclature_type_site


def to_csv(header: list[str], data: list[dict]):
    """Permet de créer des objets texte formattés pour être postés sur ODK Collect


    :param header: liste de noms de colonne pour le fichier csv
    :type header: list
    :param data: données à poster formattés en dictionnaires
    :type data: list[dict]
    """

    temp_csv = tempfile.NamedTemporaryFile(delete=False)
    with open(temp_csv.name, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    res = None
    with open(temp_csv.name, "r") as csvfile:
        res = csvfile.read()
    os.unlink(temp_csv.name)
    return res


# Décommenter ceci pour avoir les fichiers csv à téléverser en vrai
"""def to_real_csv(file_name, header: list[str], data: list[dict]):
    with open(file_name, "w") as file:
        writer = csv.DictWriter(file, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow(row)"""


def to_wkb(geojson):
    """reformats the geographic data as a WKB

    Keyword arguments:
    argument -- geoJSON geography
    Return: WKB geography
    """
    # Fonctionne avec tout sauf polygone avec précision (4ème val dans une coordonnée)
    if geojson["type"] == "Polygon":
        for coord in geojson["coordinates"]:
            for c in coord:
                if len(c) == 4:
                    c.pop(-1)
    geom = transform(lambda x, y, z=None: (x, y), shape(geojson))
    return from_shape(geom, srid=4326)


# def format_coords(geom):
#     """removes the z coordinate of a geoJSON

#     Keyword arguments:
#     geom -- geoJSON geography
#     Return: the argument as just x and y coordinates
#     """
#     if geom["type"] != "Point":
#         for coords in geom["coordinates"]:
#             if len(coords) == 3:
#                 coords.pop(-1)
#             if len(coords) == 4:
#                 coords.pop(-1)
#                 coords.pop(-1)

#     if geom["type"] == "Point":
#         p = geom["coordinates"]
#         if len(p) == 3:
#             p.pop(-1)
#         if len(p) == 4:
#             p.pop(-1)


#             p.pop(-1)
