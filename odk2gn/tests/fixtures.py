import pytest, csv
import uuid

from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import to_wkt
from geonature.utils.env import db
from geonature import create_app
from geonature.core.gn_meta.models import TDatasets
from sqlalchemy.event import listen, remove
from geonature.core.gn_commons.models import TModules

from pypnusershub.db.models import UserList, User
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from geonature.core.gn_monitoring.models import TBaseSites, corSiteModule
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringSitesGroups,
)
from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms
from utils_flask_sqla.tests.utils import JSONClient

point = {"geometry": {"type": "Point", "coordinates": [6.0535113, 44.5754145]}}

type_nom = BibNomenclaturesTypes(mnemonique="TEST", label_default="test", label_fr="Test")


@pytest.fixture(scope="function")
def test():
    with db.session.begin_nested():
        obs = User(identifiant="bidule", nom_role="bidule", prenom_role="bidule")
        db.session.add(obs)
    return obs


@pytest.fixture(scope="function")
def bidule2():
    with db.session.begin_nested():
        obs_list = UserList(code_liste="test_list", nom_liste="test_liste")
        db.session.add(obs_list)
        db.session.commit()
    return obs_list


def create_nomenclature(nomenclature_type, cd_nomenclature, label_default, label_fr):
    nom = TNomenclatures(
        id_type=nomenclature_type.id_type,
        cd_nomenclature=cd_nomenclature,
        label_default=label_default,
        label_fr=label_fr,
    )
    return nom


@pytest.fixture(scope="function")
def taxon_and_list():
    picto = db.session.query(BibListes.picto).filter(BibListes.code_liste == "100").first()
    taxon = db.session.query(Taxref).filter_by(nom_complet="Homo sapiens Linnaeus, 1758").first()
    with db.session.begin_nested():
        tax_nom = BibNoms(cd_nom=taxon.cd_nom, cd_ref=taxon.cd_nom, nom_francais=taxon.nom_vern)
        taxon_test_list = BibListes(code_liste="test_list", nom_liste="Liste test", picto=picto)
        cnl = CorNomListe(bib_nom=tax_nom, bib_liste=taxon_test_list)
        tax_nom.listes.append(cnl)
        taxon_test_list.cnl.append(cnl)
        db.session.add(tax_nom, taxon_test_list)
    return {"taxon": taxon, "tax_list": taxon_test_list}


@pytest.fixture()
def submissions(site, observers_and_list):
    sub = [
        {
            "sub_id": 1,
            "taxon": "Homo sapiens",
            "id_base_site": site.id_base_site,
            "base_site_name": site.base_site_name,
            "visit_1": {"observaters": [{"id_role": observers_and_list["user_list"][0].id_role}]},
            "observations": [],
        },
        {
            "sub_id": 22,
            "taxon": "Nardus stricta",
            "id_base_site": site.id_base_site,
            "base_site_name": site.base_site_name,
            "visit_1": {
                "observaters": [{"id_role": observers_and_list["user_list"][0].id_role}],
                "observations": [],
            },
        },
    ]

    return sub


@pytest.fixture(scope="function")
def datasets():
    return [
        TDatasets(id_dataset=1, dataset_name="ds1"),
        TDatasets(id_dataset=2, dataset_name="ds2"),
    ]


@pytest.fixture(scope="function")
def module():
    with db.session.begin_nested():
        new_module = TMonitoringModules(
            module_code="MODULE_1",
            module_label="module_1",
            module_path="module_1",
            active_frontend=True,
            active_backend=False,
        )
        db.session.add(new_module)
    return new_module


@pytest.fixture(scope="function")
def header():
    return ["column1", "column2"]


@pytest.fixture(scope="function")
def data():
    return [["1", "2"], ["3", "4"]]


@pytest.fixture
def the_csv(header, data):
    with open("test.csv", "w") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(header)
        writer.writerows(data)
        file.close()
    return file


@pytest.fixture(scope="function")
def nomenclature():
    with db.session.begin_nested():
        db.session.add(type_nom)
        db.session.flush()
        nomenclature = create_nomenclature(type_nom, "test", "test", "test")
        nomenclature.active = True
        db.session.add(nomenclature)
    return nomenclature


@pytest.fixture(scope="function")
def site(module):
    site_type = (
        db.session.query(BibNomenclaturesTypes)
        .filter(BibNomenclaturesTypes.mnemonique == "TYPE_SITE")
        .one()
    )

    with db.session.begin_nested():
        # a créer en dehors de la fonction
        nom = create_nomenclature(
            nomenclature_type=site_type,
            cd_nomenclature="test_site",
            label_default="test_site",
            label_fr="Site Test",
        )
        nom.active = True
        db.session.add(nom)
        db.session.flush()

        mon_site = TMonitoringSites(
            base_site_name="test_site",
            geom=to_wkt(point["geometry"]),
            id_nomenclature_type_site=nom.id_nomenclature,
            id_module=module.id_module,
        )
        mon_site.modules.append(module)

        module.sites.append(mon_site)
        db.session.add(mon_site)

    return mon_site


@pytest.fixture(scope="function")
def observers_and_list():
    with db.session.begin_nested():
        obs_list = UserList(code_liste="test_list", nom_liste="test_liste")
        obs = User(
            identifiant="test", groupe=False, active=True, nom_role="User", prenom_role="test"
        )
        obs_list.users.append(obs)
        db.session.add(obs)
        db.session.add(obs_list)
    return {"list": obs_list, "user_list": obs_list.users}


[
    {
        "__id": "uuid:e7f07ff5-35ca-4184-aa92-2f137bcebe35",
        "start": "2023-06-14T12:00:46.971+02:00",
        "end": "2023-06-14T12:01:13.191+02:00",
        "day": "2023-06-14",
        "deviceid": "odk-test.cevennes-parcnational.net:zgUu1bxrv1KQfdaO",
        "presentation": None,
        "method_site_choice": "map",
        "visit_point": {"site_list": None, "site_map": "20"},
        "id_base_site": "20",
        "base_site_name": "placette_1",
        "visit_1": {
            "visit_date_min": "2023-06-14T12:00:46.983+02:00",
            "visit_date_max": "2023-06-14T12:00:46.989+02:00",
            "hauteur_nard": 1,
            "hauteur_moy_vegetation": 1,
            "id_nomenclature_tech_collecte_campanule": None,
            "observers@odata.navigationLink": "Submissions('uuid%3Ae7f07ff5-35ca-4184-aa92-2f137bcebe35')/visit_1/observers",
            "observers": [{"id_role": "3", "__id": "419e8f3d180d9770eb46577c85ef9a29951d290f"}],
        },
        "medias_visit": None,
        "dataset": {"id_dataset": None, "comments_visit": None},
        "meta": {"instanceID": "uuid:e7f07ff5-35ca-4184-aa92-2f137bcebe35"},
        "__system": {
            "submissionDate": "2023-06-14T09:59:43.639Z",
            "updatedAt": None,
            "submitterId": "98",
            "submitterName": "Xavier Davis",
            "attachmentsPresent": 0,
            "attachmentsExpected": 0,
            "status": None,
            "reviewState": None,
            "deviceId": None,
            "edits": 0,
            "formVersion": "2023-05-26 12:14:25.534367",
        },
        "observations@odata.navigationLink": "Submissions('uuid%3Ae7f07ff5-35ca-4184-aa92-2f137bcebe35')/observations",
        "observations": [
            {
                "sp_choice": {"cd_nom": "195069", "pourcentage_recouvrement": 100},
                "sp_label": None,
                "sp_nbre": {"comments_observation": None},
                "medias_observation": None,
                "__id": "f21f5277f567b332aadebb3a388cc203debf8123",
            }
        ],
    }
]
