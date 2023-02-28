import logging
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func
from geonature.utils.env import DB
from geonature.core.users.models import VUserslistForallMenu
from geonature.core.gn_meta.models import TDatasets
from geonature.core.gn_monitoring.models import TBaseSites, corSiteModule
from gn_module_monitoring.monitoring.models import TMonitoringModules

from pypnnomenclature.models import (
    TNomenclatures,
    BibNomenclaturesTypes,
    CorTaxrefNomenclature,
)

from odk2gn.monitoring_config import get_nomenclatures_fields
from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms

log = logging.getLogger("app")


def get_modules_info(module_code: str):
    try:
        module = TMonitoringModules.query.filter(
            TMonitoringModules.module_code.ilike(module_code)
        ).one()
        return module
    except NoResultFound:
        log.error(f"No GeoNature module found for {module_code.lower()}")
        raise


def get_gn2_attachments_data(
    module: TMonitoringModules,
    skip_taxons: bool = False,
    skip_observers: bool = False,
    skip_jdd: bool = False,
    skip_sites: bool = False,
    skip_nomenclatures: bool = False,
):
    files = {}
    # Taxon
    if not skip_taxons:
        data = get_taxon_list(module.id_list_taxonomy)
        files["gn_taxons.csv"] = to_csv(
            header=("cd_nom", "nom_complet", "nom_vern"), data=data
        )
    # Observers
    if not skip_observers:
        data = get_observer_list(module.id_list_observer)
        files["gn_observateurs.csv"] = to_csv(
            header=("id_role", "nom_complet"), data=data
        )
    # JDD
    if not skip_jdd:
        data = get_jdd_list(module.datasets)
        files["gn_jdds.csv"] = to_csv(header=("id_dataset", "dataset_name"), data=data)
    # Sites
    if not skip_sites:
        data = get_site_list(module.id_module)
        files["gn_sites.csv"] = to_csv(
            header=("id_base_site", "base_site_name", "geometry"), data=data
        )

    # Nomenclature
    if not skip_nomenclatures:
        n_fields = []
        for niveau in ["site", "visit", "observation"]:
            n_fields = n_fields + get_nomenclatures_fields(
                module_code=module.module_code, niveau=niveau
            )

        nomenclatures = get_nomenclature_data(n_fields)
        files["gn_nomenclature.csv"] = to_csv(
            header=(
                "mnemonique",
                "id_nomenclature",
                "cd_nomenclature",
                "label_default",
            ),
            data=nomenclatures,
        )
    return files


def get_taxon_list(id_liste: int):
    """Return tuple of Taxref for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = (
        DB.session.query(
            Taxref.cd_nom, Taxref.lb_nom, func.split_part(Taxref.nom_vern, ",", 1)
        )
        .filter(BibNoms.cd_nom == Taxref.cd_nom)
        .filter(BibNoms.id_nom == CorNomListe.id_nom)
        .filter(CorNomListe.id_liste == id_liste)
        .all()
    )
    return data


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
        .filter(TBaseSites.modules.any(id_module=id_module))
        .all()
    )
    return data


def get_observer_list(id_liste: int):
    """Return tuple of Observers for id_liste

    :param id_liste: Identifier of the taxref list
    :type id_liste: int
    """
    data = DB.session.query(
        VUserslistForallMenu.id_role, VUserslistForallMenu.nom_complet
    ).filter_by(id_menu=id_liste)
    return data


def get_jdd_list(datasets: []):
    """Return tuple of Dataset

    :param datasets: List of associated dataset
    :type datasets: []
    """
    ids = [jdd.id_dataset for jdd in datasets]
    data = DB.session.query(TDatasets.id_dataset, TDatasets.dataset_name).filter(
        TDatasets.id_dataset.in_(ids)
    )
    return data


def get_ref_nomenclature_list(
    code_nomenclature_type: str,
    cd_nomenclatures: [] = None,
    regne: str = None,
    group2_inpn: str = None,
):
    q = (
        DB.session.query(
            BibNomenclaturesTypes.mnemonique,
            TNomenclatures.id_nomenclature,
            TNomenclatures.cd_nomenclature,
            TNomenclatures.label_default,
        )
        .filter(BibNomenclaturesTypes.id_type == TNomenclatures.id_type)
        .filter(BibNomenclaturesTypes.mnemonique == code_nomenclature_type)
    )
    if cd_nomenclatures:
        q = q.filter(TNomenclatures.cd_nomenclature.in_(cd_nomenclatures))

    if regne:
        q = q.filter(
            CorTaxrefNomenclature.id_nomenclature == TNomenclatures.id_nomenclature
        ).filter(CorTaxrefNomenclature.regne == regne)
        if group2_inpn:
            q = q.filter(CorTaxrefNomenclature.group2_inpn == group2_inpn)

    return q.all()


def get_nomenclature_data(nomenclatures_fields):
    data = []
    for f in nomenclatures_fields:
        data = data + get_ref_nomenclature_list(**f)
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
