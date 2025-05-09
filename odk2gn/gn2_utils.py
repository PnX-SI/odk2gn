import logging
import os
import csv
from shapely.geometry import shape
from shapely.ops import transform
from geoalchemy2.shape import from_shape
from sqlalchemy.exc import SQLAlchemyError


import tempfile
from geonature.utils.env import DB
from geonature.core.users.models import VUserslistForallMenu
from geonature.core.gn_commons.models import TModules
from geonature.utils.config import config
from geonature.utils.utilsmails import send_mail

from pypnusershub.db.models import User
from pypnnomenclature.models import TNomenclatures, CorTaxrefNomenclature

from apptax.taxonomie.models import Taxref, CorNomListe, BibNoms

from odk2gn.odk_api import update_review_state

log = logging.getLogger("app")


def get_module_code(id_module: int):
    module_code = (TModules.query.filter_by(id_module=id_module).one()).module_code
    return module_code

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


def get_observers(observers_list):
    obss = DB.session.query(User).filter(User.id_role.in_(tuple(observers_list))).all()
    return obss


def get_taxon_list(id_liste: int):
    """Return dict of Taxref
    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = (
        DB.session.query(Taxref)
        .order_by(Taxref.nom_complet)
        .filter(BibNoms.cd_nom == Taxref.cd_nom)
        .filter(BibNoms.id_nom == CorNomListe.id_nom)
        .filter(CorNomListe.id_liste == id_liste)
        .limit(3000)
    )
    taxons = []
    for tax in data:
        tax = tax.as_dict()
        if tax["nom_vern"] is not None:
            tax["nom_complet"] = tax["nom_complet"] + " - " + tax["nom_vern"]
        taxons.append(tax)
    return taxons


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

def commit_data(project_id, form_id, sub_id):
    try:
        DB.session.commit()
        update_review_state(project_id, form_id, sub_id, "approved")
    except SQLAlchemyError as e:
        log.error("Error while posting data")
        log.error(str(e))
        send_mail(
            config["gn_odk"]["email_for_error"],
            subject="Synchronisation ODK error",
            msg_html=str(e),
        )
        update_review_state(project_id, form_id, sub_id, "hasIssues")
        DB.session.rollback()

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
