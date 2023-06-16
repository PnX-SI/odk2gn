import pytest, csv
import uuid
import datetime
from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import to_wkt
from geonature.utils.env import db
from geonature import create_app
from geonature.core.gn_meta.models import TDatasets
from sqlalchemy.event import listen, remove
from geonature.core.gn_commons.models import TModules
from gn_module_monitoring.config.repositories import get_config
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
def submissions(site, observers_and_list, module, taxon_and_list):
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "id_base_site": site.id_base_site,
            "base_site_name": site.base_site_name,
            "visit": {
                "visit_date_min": datetime.date.today(),
                "id_module": module.id_module,
                "observers": [{"id_role": observers_and_list["user_list"][0].id_role}],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": 1},
            "observations": [{"cd_nom": taxon_and_list["taxon"].cd_nom, "comptage": 1}],
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


# _get_schema_fields_data


@pytest.fixture(scope="function")
def mon_schema_fields():
    return [
        {
            "path": "/start",
            "name": "start",
            "type": "dateTime",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/end",
            "name": "end",
            "type": "dateTime",
            "binary": None,
            "selectMultiple": None,
        },
        {"path": "/day", "name": "day", "type": "date", "binary": None, "selectMultiple": None},
        {
            "path": "/deviceid",
            "name": "deviceid",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/presentation",
            "name": "presentation",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/method_site_choice",
            "name": "method_site_choice",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_point",
            "name": "visit_point",
            "type": "structure",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_point/site_list",
            "name": "site_list",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_point/site_map",
            "name": "site_map",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/id_base_site",
            "name": "id_base_site",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/base_site_name",
            "name": "base_site_name",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_1",
            "name": "visit_1",
            "type": "structure",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_1/visit_date_min",
            "name": "visit_date_min",
            "type": "dateTime",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_1/visit_date_max",
            "name": "visit_date_max",
            "type": "dateTime",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_1/observers",
            "name": "observers",
            "type": "repeat",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/visit_1/observers/id_role",
            "name": "id_role",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/dataset",
            "name": "dataset",
            "type": "structure",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/dataset/id_dataset",
            "name": "id_dataset",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/dataset/comments_visit",
            "name": "comments_visit",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/observations",
            "name": "observations",
            "type": "repeat",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/meta",
            "name": "meta",
            "type": "structure",
            "binary": None,
            "selectMultiple": None,
        },
        {
            "path": "/meta/instanceID",
            "name": "instanceID",
            "type": "string",
            "binary": None,
            "selectMultiple": None,
        },
    ]


@pytest.fixture(scope="function")
def my_config():
    return get_config()


@pytest.fixture(scope="function")
def attachment():
    return ""


@pytest.fixture(scope="function")
def visit(submissions):
    return submissions[0]["site"]["visit"]


{
    "__id": "uuid:4602b51f-557c-4232-af32-7ecf657e25fe",
    "id_base_site": "6494",
    "base_site_name": "Maison Deroy",
    "visit_1": {
        "visit_date_min": "2023-05-24T14:27:00.000+02:00",
        "observers": [{"id_role": "1604", "__id": "1f7495d11ab7477b290f7cf8349e272d984c66a9"}],
    },
    "dataset": {
        "id_dataset": None,
    },
    "no_data": "chiro",
    "observations@odata.navigationLink": "Submissions('uuid%3A4602b51f-557c-4232-af32-7ecf657e25fe')/observations",
    "observations": [
        {
            "sp_choice": {"cd_nom": "186233"},
            "id_nomenclature_behaviour": None,
            "id_nomenclature_bio_condition": None,
            "id_nomenclature_bio_status": None,
            "id_nomenclature_obs_technique": None,
            "id_nomenclature_life_stage": None,
            "id_nomenclature_sex": None,
            "sp_label": None,
            "sp_nbre": {"count_min": 1, "count_max": 1, "comments_observation": None},
            "medias_observation": None,
            "__id": "f531cb5d8c817cdd8b9ee64f4019a0e3f27ff89f",
        }
    ],
}
