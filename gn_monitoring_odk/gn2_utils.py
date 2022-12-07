
from sqlalchemy.orm.exc import NoResultFound
from geonature.utils.env import DB
from geonature.core.users.models import (
    VUserslistForallMenu
)
from geonature.core.gn_meta.models import TDatasets
from geonature.core.gn_monitoring.models import TBaseSites, corSiteModule
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules
)
from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms

import csv

def get_modules_info(module_code: str):
        try:
            module = TMonitoringModules.query.filter_by(
                module_code=module_code
            ).one()
            return module
        except NoResultFound:
            return None

def get_gn2_attachments_data(
        module:TMonitoringModules,
        id_nomeclature_type : []
    ):
        files = {}
        data = get_taxon_list(module.id_list_taxonomy)
        files['gn_taxons.csv'] = to_csv(
            header=("cd_nom", "nom_complet", "nom_vern"),
            data=data
        )
        data = get_observer_list(module.id_list_observer)
        files['gn_observateurs.csv'] = to_csv(
            header=("id_role", "nom_complet"),
            data=data
        )
        data = get_jdd_list(module.datasets)
        files['gn_jdds.csv'] = to_csv(
            header=("id_role", "nom_complet"),
            data=data
        )
        data = get_site_list(module.sites)
        files['gn_sites.csv'] = to_csv(
            header=("id_base_site", "base_site_name"),
            data=data
        )

        return files


def get_taxon_list(id_liste: int):
    """Return tuple of Taxref for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = (
        DB.session.query(Taxref.cd_nom, Taxref.nom_complet, Taxref.nom_vern)
        .filter(BibNoms.cd_nom == Taxref.cd_nom)
        .filter(BibNoms.id_nom == CorNomListe.id_nom)
        .filter(CorNomListe.id_liste == id_liste)
        .all()
    )
    return data


def get_site_list(sites: []):
    """Return tuple of TBase site for module

    :param sites: Liste des sites
    :type id_liste: []
    """
    data = [(s.id_base_site, s.base_site_name) for s in sites]
    return data


def get_observer_list(id_liste: int):
    """Return tuple of Observers for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = DB.session.query(VUserslistForallMenu.id_role, VUserslistForallMenu.nom_complet).filter_by(id_menu=id_liste)
    return data

def get_jdd_list(datasets: []):
    """Return tuple of Dataset

    :param datasets: List of associated dataset
    :type datasets: []
    """
    ids = [jdd.id_dataset for jdd in datasets]
    data = DB.session.query(
        TDatasets.id_dataset, TDatasets.dataset_name
    ).filter(TDatasets.id_dataset.in_(ids))
    return data

def to_csv(header, data):
    """Return tuple in csv format

    :param header: _description_
    :type header: _type_
    :param data: _description_
    :type data: _type_
    :return: _description_
    :rtype: _type_
    """
    out = []
    out.append(",".join(header))
    for d in data:
        out.append(",".join(map(str, d)))
    return "\n".join(out)