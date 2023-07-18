import logging
import click
import uuid
import csv
import json
import geojson
from gn_module_priority_flora.models import TZprospect, TApresence, CorApPerturbation

from shapely.geometry import shape
import flatdict
from sqlalchemy.orm import exc
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy

from odk2gn.odk_api import ODKSchema, get_submissions, update_review_state, client
from odk2gn.gn2_utils import to_csv, get_taxon_list, get_observer_list
from pyodk.client import Client
from datetime import datetime
from geonature.utils.env import DB
from geonature.utils.config import config as geonature_config
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature
from geonature.core.gn_meta.models import TDatasets
from pypnusershub.db.models import UserList, User
from geonature.core.users.models import VUserslistForallMenu

from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms

from geonature.app import create_app
from geonature.utils.env import BACKEND_DIR
from geonature.core.gn_commons.models import BibTablesLocation


log = logging.getLogger("app")


def get_id_taxon_liste(code_liste):
    """gets the list ids for the taxons

    Keyword arguments:
    code_liste -- code string for the list
    Return: id_liste int
    """

    id = DB.session.query(BibListes.id_liste).filter(BibListes.code_liste == code_liste).first()
    return id


def get_id_observer_liste(code_liste):
    """gets the list ids for the observers

    Keyword arguments:
    code_liste -- code string for the list
    Return: id_liste int
    """
    id = DB.session.query(UserList.id_liste).filter(UserList.code_liste == code_liste).first()
    return id


def get_nomenclatures():
    # returns the list of nomenclatures
    nomenclatures = [
        "TYPE_PERTURBATION",
        "INCLINE_TYPE",
        "PHYSIOGNOMY_TYPE",
        "HABITAT_STATUS",
        "THREAT_LEVEL",
        "PHENOLOGY_TYPE",
        "FREQUENCY_METHOD",
        "COUNTING_TYPE",
    ]
    res = []
    q = TNomenclatures.query.join(TNomenclatures.nomenclature_type, aliased=True).filter(
        BibNomenclaturesTypes.mnemonique.in_(nomenclatures)
    )
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


def write_files():
    # updates the csv file attachments on ODK central
    files = {}
    nomenclatures = get_nomenclatures()
    nom_header = ["mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"]
    files["pf_nomenclatures.csv"] = to_csv(nom_header, nomenclatures)
    taxons = get_taxon_list(
        get_id_taxon_liste(geonature_config["PRIORITY_FLORA"]["taxons_list_code"])
    )
    taxon_header = ["cd_nom", "nom_complet", "nom_vern"]
    files["pf_taxons.csv"] = to_csv(taxon_header, taxons)
    observers = get_observer_list(
        get_id_observer_liste(geonature_config["PRIORITY_FLORA"]["observers_list_code"])
    )
    obs_header = ["id_role", "nom_complet"]
    files["pf_observers.csv"] = to_csv(obs_header, observers)
    return files


def nomenclature_to_int(val):
    """formats the nomenclature id data for the db

    Keyword arguments:
    argument -- id_nomenclature as string
    Return: id_nomenclature
    """

    org_val = val
    try:
        val = int(val)
    except:
        val = org_val
    return val


def to_wkt(geom):
    """reformats the geographic data as a WKT

    Keyword arguments:
    argument -- geoJSON geography
    Return: WKT geography
    """

    s = json.dumps(geom)
    g1 = geojson.loads(s)
    g2 = shape(g1)
    return g2.wkt


def format_coords(geom):
    """removes the z coordinate of a geoJSON

    Keyword arguments:
    geom -- geoJSON geography
    Return: the argument as just x and y coordinates
    """

    if geom["type"] == "Polygon":
        for coords in geom["coordinates"]:
            for point in coords:
                if len(point) == 3:
                    point.pop(-1)
                if len(point) == 4:
                    point.pop(-1)
                    point.pop(-1)

    if geom["type"] == "Point":
        p = geom["coordinates"]
        if len(p) == 3:
            p.pop(-1)
        if len(p) == 4:
            p.pop(-1)
            p.pop(-1)


def get_nomenclature(id_nomenclature):
    """gets the corresponding nomenclature object

    Keyword arguments:
    id_nomenclature -- int
    Return: TNomenclature object
    """

    nom = (
        DB.session.query(TNomenclatures)
        .filter(TNomenclatures.id_nomenclature == id_nomenclature)
        .first()
    )
    return nom


def get_nomenclature_id(type_mnemonique, cd_nomenclature):
    """gets the id of the corresponding nomenclature object

    Keyword arguments:
    type_mnemonique -- string representing the type of nomenclature
    cd_nomenclature -- code representing the user value for the nomenclature
    Return: id_nomenclature : corresponding nomenclature id
    """

    id = (
        DB.session.query(TNomenclatures.id_nomenclature)
        .filter(BibNomenclaturesTypes.mnemonique == type_mnemonique)
        .filter(BibNomenclaturesTypes.id_type == TNomenclatures.id_type)
        .filter(TNomenclatures.cd_nomenclature == cd_nomenclature)
        .first()
    )
    return id


def get_user(id_role):
    """gets the db user object

    Keyword arguments:
    id_role -- int
    Return: user
    """

    user = DB.session.query(User).filter(User.id_role == id_role).first()
    return user


def update_priority_flora_db(project_id, form_id):
    # adds the new ODK submissions to the db
    # gets the new ODK submissions
    form_data = get_submissions(project_id, form_id)
    # gets the dataset id, which is fixed
    id_dataset = (
        DB.session.query(TDatasets.id_dataset)
        .filter(TDatasets.dataset_shortname == "PRIORITY_FLORA")
        .first()
    )
    for sub in form_data:
        # create and seed the prospection zone object
        zp = TZprospect()
        zp.id_dataset = id_dataset
        # format the geographical coordinates in WKT with no z coordinate
        format_coords(sub["zp_geom_4326"])
        zp.geom_4326 = to_wkt(sub["zp_geom_4326"])
        zp.cd_nom = sub["cd_nom"]
        zp.date_min = sub["date_min"]
        zp.date_max = sub["date_min"]
        zp.area = sub["zp_area"]
        zp.initial_insert = "ODK"
        zp.observers = []
        # manage observer list
        observers = sub["observers"].split(" ")
        for observer in observers:
            id_role = nomenclature_to_int(observer)
            obs = get_user(id_role)
            zp.observers.append(obs)
        DB.session.add(zp)
        for ap in sub["aps"]:
            # create and seed the presence area object
            t_ap = TApresence()
            t_ap.id_zp = zp.id_zp
            if ap["type_geom"] == "point":
                ap_geom_4326 = ap["ap_geom_point"]
                area = ap["situation"]["ap_area_point"]
            if ap["type_geom"] == "shape":
                ap_geom_4326 = ap["ap_geom_shape"]
                area = ap["situation"]["ap_area_shape"]
            format_coords(ap_geom_4326)
            t_ap.geom_4326 = to_wkt(ap_geom_4326)
            t_ap.area = area
            t_ap.altitude_min = None
            t_ap.altitude_max = None
            # situation : all of the geographical info for the ap
            situation = ap["situation"]
            t_ap.id_nomenclature_incline = nomenclature_to_int(
                situation["id_nomenclature_incline"]
            )
            # habitat : all the information about the habitat of the flora
            habitat = ap["habitat"]
            t_ap.id_nomenclature_habitat = nomenclature_to_int(habitat["id_nomenclature_habitat"])
            t_ap.favorable_status_percent = habitat["favorable_status_percent"]
            t_ap.id_nomenclature_threat_level = get_nomenclature_id(
                "THREAT_LEVEL", habitat["threat_level"]
            )
            t_ap.id_nomenclature_phenology = nomenclature_to_int(ap["id_nomenclature_phenology"])
            # frequency : how the frequency was estimated
            frequency_est = ap["frequency_est"]
            t_ap.id_nomenclature_frequency_method = nomenclature_to_int(
                frequency_est["id_nomenclature_frequency_method"]
            )
            t_ap.frequency = frequency_est["frequency"]
            # count : number of individuals and how they were counted
            count = ap["count"]
            if (
                count["counting_method"] == "1"
            ):  # counting all individuals, so we have only one value for both min and max
                t_ap.total_max = count["num"]
                t_ap.total_min = count["num"]
            elif (
                count["counting_method"] == "2"
            ):  # estimating from a sample, so min value and max value
                t_ap.total_max = count["total_max"]
                t_ap.total_min = count["total_min"]
                if t_ap.total_max == t_ap.total_min:
                    log.warning("min and max values are equal")
            else:  # no count
                t_ap.total_max = None
                t_ap.total_min = None
            t_ap.id_nomenclature_counting = get_nomenclature_id(
                "COUNTING_TYPE", count["counting_method"]
            )
            t_ap.comment = ap["comment"]
            # handling perturbations and physiognomies
            t_ap.perturbations = []
            t_ap.physiognomies = []
            if situation["physiognomies"] is not None:
                physiognomies = situation["physiognomies"].split(" ")
                for physiog in physiognomies:
                    id_physiog = nomenclature_to_int(physiog)
                    phys = get_nomenclature(id_physiog)
                    t_ap.physiognomies.append(phys)
            if habitat["perturbations"] is not None:
                perturbations = habitat["perturbations"].split(" ")
                for perturb in perturbations:
                    id_perturb = nomenclature_to_int(perturb)
                    pert = get_nomenclature(id_perturb)
                    t_ap.perturbations.append(pert)
                # implementation depends on db implementation of effective_presence
                """    c_ap_perturb = CorApPerturbation()
                    c_ap_perturb.id_nomenclature = id_perturb
                    c_ap_perturb.id_ap = t_ap.id_ap
                    
                    if habitat['threat_level']=='3':
                        c_ap_perturb.effective_presence = True
                    DB.session.add(c_ap_perturb) """
            zp.ap.append(t_ap)
            DB.session.add(t_ap)

        try:
            DB.session.commit()
            update_review_state(project_id, form_id, sub["__id"], "approved")
        except SQLAlchemyError as e:
            log.error("Error while posting data")
            log.error(str(e))
            update_review_state(project_id, form_id, sub["__id"], "hasIssues")
            DB.session.rollback()
