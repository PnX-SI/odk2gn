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

from odk2gn.odk_api import ODKSchema,get_submissions, update_review_state
from odk2gn.gn2_utils import to_csv
from pyodk.client import Client
from datetime import datetime
from geonature.utils.env import DB
from geonature.utils.config import config as geonature_config
from pypnnomenclature.models import (
    TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature
)
from geonature.core.gn_meta.models import TDatasets
from pypnusershub.db.models import UserList, User
from geonature.core.users.models import (
    VUserslistForallMenu
)

from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms

from geonature.app import create_app
from geonature.utils.env import BACKEND_DIR
from geonature.core.gn_commons.models import BibTablesLocation

client = Client('config.toml')
log = logging.getLogger("app")


def get_taxons():
#returns the list of taxons
    code_liste = geonature_config["PRIORITY_FLORA"]["taxons_list_code"]
    data = (
        DB.session.query(Taxref.cd_nom, Taxref.nom_complet, Taxref.nom_vern)
        .filter(BibNoms.cd_nom == Taxref.cd_nom)
        .filter(BibNoms.id_nom == CorNomListe.id_nom)
        .filter(CorNomListe.id_liste == BibListes.id_liste)
        .filter(BibListes.code_liste == code_liste)
        .all()
    )
    header = ['cd_nom','nom_complet','nom_vern']
    return {'header': header, 'data': data}


def get_observers():
#returns the list of observers
    code_liste = geonature_config["PRIORITY_FLORA"]['observers_list_code']
    data = (
        DB.session.query(VUserslistForallMenu.id_role, VUserslistForallMenu.nom_complet)
        .filter(UserList.id_liste == VUserslistForallMenu.id_menu)
        .filter(UserList.code_liste == code_liste))
    header=['id_role','nom_complet']
    return {'header' : header, 'data': data}


def get_nomenclatures():
#returns the list of nomenclatures
    nomenclatures = ['TYPE_PERTURBATION', 'INCLINE_TYPE', 'PHYSIOGNOMY_TYPE', 'HABITAT_STATUS', 'THREAT_LEVEL', 'PHENOLOGY_TYPE', 'FREQUENCY_METHOD', 'COUNTING_TYPE']
    data = DB.session.query(
        BibNomenclaturesTypes.mnemonique,
        TNomenclatures.id_nomenclature,
        TNomenclatures.cd_nomenclature,
        TNomenclatures.label_default
    ).filter(
        BibNomenclaturesTypes.id_type == TNomenclatures.id_type
    ).filter(
        BibNomenclaturesTypes.mnemonique.in_(nomenclatures)
    )
    header=['mnemonique','id_nomenclature','cd_nomenclature','label_default']
    return {'header': header, 'data': data}


def write_files():
#updates the csv file attachments on ODK central
    files={}
    nomenclatures = get_nomenclatures()
    files['pf_nomenclatures.csv'] = to_csv(
                                nomenclatures['header'],
                                nomenclatures['data'])
    taxons = get_taxons()
    files['pf_taxons.csv'] = to_csv(
               taxons['header'], 
               taxons['data'])
    observers = get_observers()
    files['pf_observers.csv'] =  to_csv( 
               observers['header'], 
               observers['data'])
    return files
    
def to_int(val):
    org_val = val
    try:
        val = int(val)
    except:
        val = org_val
    return val 

def to_wkt(geom):
    s = json.dumps(geom)
    g1 = geojson.loads(s)
    g2 = shape(g1)
    return g2.wkt

def format_coords(geom):
    for coords in geom['coordinates']:
        for point in coords:
            point.pop(-1)

def get_nomenclature(id_nomenclature):
    nom = DB.session.query(TNomenclatures).filter(
        TNomenclatures.id_nomenclature == id_nomenclature
        ).first()
    return nom

def get_nomenclature_id(type_mnemonique, cd_nomenclature):
    id = DB.session.query(TNomenclatures.id_nomenclature).filter(
        BibNomenclaturesTypes.mnemonique == type_mnemonique
    ).filter(
        BibNomenclaturesTypes.id_type == TNomenclatures.id_type
    ).filter(
        TNomenclatures.cd_nomenclature == cd_nomenclature
        ).first()
    return id

def get_user(id_role):
    user = DB.session.query(User).filter(
        User.id_role == id_role
    ).first()
    return user



def update_priority_flora_db(project_id, form_id):
#adds the new ODK submissions to the db
    form_data = get_submissions(project_id, form_id)
    id_dataset = DB.session.query(TDatasets.id_dataset).filter(TDatasets.dataset_shortname=='PRIORITY_FLORA').first()
    for sub in form_data :
        print(sub)
        zp = TZprospect()
        zp.id_dataset = id_dataset
        format_coords(sub['zp_geom_4326'])
        zp.geom_4326 = to_wkt(sub['zp_geom_4326'])
        zp.cd_nom =  sub['cd_nom']
        zp.date_min= sub['date_min']
        zp.date_max = sub['date_max']
        zp.area = sub['zp_area']
        zp.initial_insert = "ODK"
        zp.observers = []
        for observer in sub['observaters']:
            print(observer)
            id_role = to_int(observer['id_role'])
            obs = get_user(id_role)
            print(obs)
            zp.observers.append(obs)
        DB.session.add(zp)
        DB.session.flush()
        for ap in sub['aps']:
            t_ap = TApresence()
            t_ap.id_zp = zp.id_zp
            format_coords(ap['ap_geom_4326'])
            t_ap.geom_4326 = to_wkt(ap['ap_geom_4326'])
            situation = ap['situation']
            t_ap.area = situation['ap_area']
            t_ap.id_nomenclature_incline = to_int(situation['id_nomenclature_incline']) or None
            habitat = ap['habitat']
            t_ap.id_nomenclature_habitat = to_int(habitat['id_nomenclature_habitat']) or None
            t_ap.favorable_status_percent = habitat['favorable_status_percent'] or None
            t_ap.id_nomenclature_threat_level = get_nomenclature_id('THREAT_LEVEL', habitat['threat_level']) or None
            t_ap.id_nomenclature_phenology = to_int(ap['id_nomenclature_phenology']) or None
            frequency_est = ap['frequency_est']
            t_ap.id_nomenclature_frequency_method = to_int(frequency_est['id_nomenclature_frequency_method']) or None
            t_ap.frequency = frequency_est['frequency'] or None
            count = ap['count']
            if count['counting_method']=='1':
                t_ap.total_max = count['num']
                t_ap.total_min = count['num']
            elif count['counting_method']=='2':
                t_ap.total_max = count['total_max']
                t_ap.total_min = count['total_min']
            else:
                t_ap.total_max = None
                t_ap.total_min = None
            t_ap.id_nomenclature_counting = get_nomenclature_id('COUNTING_TYPE', count['counting_method']) or None
            t_ap.comment = ap['comment']
            t_ap.perturbations = []
            t_ap.physiognomies = []
            if situation['physiognomies'] is not None:
                physiognomies = situation['physiognomies'].split(' ')
                for physiog in physiognomies:
                    id_physiog = to_int(physiog)
                    phys = get_nomenclature(id_physiog)
                    t_ap.physiognomies.append(phys)
            if habitat['perturbations'] is not None:
                perturbations = habitat['perturbations'].split(' ')
                for perturb in perturbations:
                    id_perturb = to_int(perturb)
                    pert = get_nomenclature(id_perturb)
                    t_ap.perturbations.append(pert)

                """    c_ap_perturb = CorApPerturbation()
                    c_ap_perturb.id_nomenclature = id_perturb
                    c_ap_perturb.id_ap = t_ap.id_ap
                    
                    if habitat['threat_level']=='3':
                        c_ap_perturb.effective_presence = True
                    DB.session.add(c_ap_perturb) """
            DB.session.add(t_ap)
        try:
            DB.session.commit()
            update_review_state(project_id, form_id, sub['__id'], 'approved')
        except SQLAlchemyError as e:
            log.error("Error while posting data")
            log.error(str(e))
            update_review_state(project_id, form_id, sub["__id"], "hasIssues")
            DB.session.rollback()

        