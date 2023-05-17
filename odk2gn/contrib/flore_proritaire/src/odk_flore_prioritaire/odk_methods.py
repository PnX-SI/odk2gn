import logging
import click
import uuid
import csv
import json
#from gn_module_flore_prioritaire.models import TZProspect, TApresence, CorApPerturbation

import flatdict
from sqlalchemy.orm import exc
from sqlalchemy.exc import SQLAlchemyError

from odk2gn.odk_api import ODKSchema
from odk2gn.gn2_utils import to_csv
from pyodk.client import Client
from datetime import datetime
from geonature.utils.env import DB
from pypnnomenclature.models import (
    TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature
)
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
    data = (
        DB.session.query(Taxref.cd_nom, Taxref.nom_complet, Taxref.nom_vern)
        .filter(BibNoms.cd_nom == Taxref.cd_nom)
        .filter(BibNoms.id_nom == CorNomListe.id_nom)
        .filter(CorNomListe.id_liste == BibListes.id_liste)
        .filter(BibListes.code_liste == '100')
        .all()
    )
    header = ['cd_nom','nom_complet','nom_vern']
    return {'header': header, 'data': data}


def get_observers():
#returns the list of observers
    id_liste=1
    data = DB.session.query(VUserslistForallMenu.id_role, VUserslistForallMenu.nom_complet).filter_by(id_menu=id_liste)
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



def draft(project_id, form_id):
#sets the ODK central entry for the form to a draft state
    with client:
        request = client.post(f"projects/{project_id}/forms/{form_id}/draft")
        assert request.status_code == 200


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
    


def upload_file(project_id, form_id, file_name, data):
    response = client.post(
        f"{client.config.central.base_url}/v1/projects/{project_id}/forms/{form_id}/draft/attachments/{file_name}",
        data=data.encode("utf-8", "strict"),
    )
    if response.status_code == 404:
        log.warning(
            f"Le fichier {file_name} n'existe pas dans la définition du formulaire"
        )
    elif response.status_code == 200:
        log.info(f"fichier {file_name} téléversé")
    else:
        # TODO raise error
        pass


def publish(project_id, form_id):
#publishes the form
    version_number = datetime.now()
    response = client.post(
        f"projects/{project_id}/forms/{form_id}/draft/publish?version={version_number}"
    )
    assert response.status_code == 200

def update_review_state(project_id, form_id, submission_id, review_state):
#updates the review state of the submissions
    token = client.session.auth.service.get_token(
        username=client.config.central.username,
        password=client.config.central.password,
    )
    review_submission_response = client.patch(
        f"{client.config.central.base_url}/v1/projects/{project_id}/forms/{form_id}/submissions/{submission_id}",
        data=json.dumps({"reviewState": review_state}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
    )
    try:
        assert review_submission_response.status_code == 200
    except AssertionError:
        log.error("Error while update submision state")

def update_odk_form(project_id, form_id):
#updates the odk form with the new csv files
    files = write_files()
    draft(project_id, form_id)
    for file_name in files:
            upload_file(project_id, form_id, file_name, files[file_name])
    publish(project_id, form_id)


def get_submissions(project_id, form_id):
    # Creation client odk central
    form_data = None
    with client:
        form_data = client.submissions.get_table(
            form_id=form_id,
            project_id=project_id,
            expand="*",
            # TODO : try received or edited (but edited not actually support)
            filter="__system/reviewState ne 'approved' and __system/reviewState ne 'hasIssues' and __system/reviewState ne 'rejected'",
            # filter="__system/reviewState eq 'rejected'",
        )
        return form_data["value"]


def to_int(dict,key):
    val = dict[key]
    org_val = val
    try:
        val = int(dict[key])
    except:
        val = org_val
    return val 

def update_priority_flora_db(project_id, form_id):
#adds the new ODK submissions to the db
    form_data = get_submissions(project_id, form_id)
    for sub in form_data :
        print(sub)
        zp = TZProspect()
        zp.geom_4326 = sub['zp_geom_4326']
        zp.cd_nom =  to_int(sub, 'cd_nom')
        zp.date_min= sub['date_min']
        zp.date_max = sub['date_max']
        zp.area = sub['zp_area']
        zp.initial_insert = "ODK"
        observaters = []
        for observer in sub['observaters']:
            id_role = int(observer['id_role'])
            observaters.append(id_role)
        DB.session.add(zp)
        for ap in sub['aps']:
            t_ap = TApresence()
            t_ap.geom_4326 = ap['ap_geom_4326']
            situation = ap['situation']
            t_ap.area = situation['ap_area']
            t_ap.id_nomenclature_incline = int(situation['id_nomenclature_incline'])
            habitat = ap['habitat']
            t_ap.id_nomenclature_habitat = int(habitat['id_nomenclature_habitat'])
            t_ap.favorable_status_percent = habitat['favorable_status_percent']
            t_ap.id_nomenclature_threat_level = int(habitat['id_nomenclature_threat_level'])
            t_ap.id_nomenclature_phenology = int(ap['id_nomenclature_phenology'])
            frequency_est = ap['frequency_est']
            t_ap.id_nomenclature_frequency_method = int(frequency_est['id_nomenclature_frequency_method'])
            t_ap.frequency = frequency_est['frequency']
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
            t_ap.id_nomenclature_counting = count['id_nomenclature_counting']
            t_ap.comment = ap['comment']
            DB.session.add(t_ap)
            if situation['physionomies'] is not None:
                physiognomies = situation['physionomies'].split(' ')
                for physiog in physiognomies:
                    id_physiog= int(physiog)
                    physiognomies[physiog] = id_physiog
            if habitat['perturbations'] is not None:
                c_ap_perturb = CorApPerturbation()
                perturbations = habitat['perturbations'].split(' ')
                for perturb in perturbations:
                    id_perturb = int(perturb)
                    c_ap_perturb.id_nomenclature = id_perturb
                    if habitat['threat_level']=='3':
                        c_ap_perturb.effective_presence = True
                DB.session.add(c_ap_perturb)
        try:
            DB.session.commit()
            update_review_state(project_id, form_id, sub['__id'], 'approved')
        except SQLAlchemyError as e:
            log.error("Error while posting data")
            log.error(str(e))
            update_review_state(project_id, form_id, sub["__id"], "hasIssues")
            DB.session.rollback()

        