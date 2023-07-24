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


@pytest.fixture(scope="function")
def site_group(module):
    with db.session.begin_nested():
        group = TMonitoringSitesGroups(
            id_module=module.id_module,
            uuid_sites_group=uuid.uuid4(),
            sites_group_name="test_group",
            sites_group_description="test",
        )
        db.session.add(group)
    return group


@pytest.fixture(scope="function")
def type_nomenclature():
    with db.session.begin_nested():
        type_nom = BibNomenclaturesTypes(mnemonique="TEST", label_default="test", label_fr="Test")
        db.session.add(type_nom)
    return type_nom


@pytest.fixture(scope="function")
def plant():
    with db.session.begin_nested():
        plant = Taxref(
            cd_nom=9999999,
            regne="Plantae",
            nom_complet="Plant Test",
            nom_vern="Plante test",
            nom_valide="Plante test",
        )
        db.session.add(plant)
    return plant


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
def taxon_and_list(plant):
    picto = "images/pictos/nopicto.gif"
    taxon = plant
    with db.session.begin_nested():
        tax_nom = BibNoms(cd_nom=taxon.cd_nom, cd_ref=taxon.cd_nom, nom_francais=taxon.nom_vern)
        taxon_test_list = BibListes(code_liste="test_list", nom_liste="Liste test", picto=picto)
        cnl = CorNomListe(bib_nom=tax_nom, bib_liste=taxon_test_list)
        tax_nom.listes.append(cnl)
        taxon_test_list.cnl.append(cnl)
        db.session.add(tax_nom, taxon_test_list)
    return {"taxon": taxon, "tax_list": taxon_test_list}


@pytest.fixture(scope="function")
def submissions(site, observers_and_list, module, taxon_and_list):
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "id_base_site": site.id_base_site,
            "base_site_name": site.base_site_name,
            "visit": {
                "visit_date_min": datetime.date.today(),
                "id_module": module.id_module,
                "media": "images/pictos/nopicto.gif",
                "comments": "test",
                "observers": [{"id_role": observers_and_list["user_list"][0].id_role}],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": 1},
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": 1,
                    "comments": "test",
                }
            ],
        },
    ]
    return sub


@pytest.fixture(scope="function")
def sub_with_site_creation(observers_and_list, module, taxon_and_list, site_group):
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "create_site": "true",
            "site_creation": {
                "site_name": "test",
                "base_site_description": "test",
                "geom": point["geometry"],
                "is_new": True,
                "site_group": site_group.id_sites_group,
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": module.id_module,
                "medias_visit": "images/pictos/nopicto.gif",
                "comments": "test",
                "observers": [
                    {
                        "observer": observers_and_list["user_list"][0],
                        "id_role": observers_and_list["user_list"][0].id_role,
                    }
                ],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": 1},
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": 1,
                    "comments": "test",
                }
            ],
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
    return [{"column1": "1", "column2": "2"}, {"column1": "3", "column2": "4"}]


@pytest.fixture
def the_csv(header, data):
    with open("test.csv", "w") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(header)
        writer.writerows(data)
        file.close()
    return file


@pytest.fixture(scope="function")
def nomenclature(type_nomenclature):
    with db.session.begin_nested():
        nomenclature = create_nomenclature(type_nomenclature, "test", "test", "test")
        nomenclature.active = True
        nomenclature.nomenclature_type = type_nomenclature
        db.session.add(nomenclature)
    return nomenclature


@pytest.fixture(scope="function")
def site_type():
    site_type = (
        db.session.query(BibNomenclaturesTypes)
        .filter(BibNomenclaturesTypes.mnemonique == "TYPE_SITE")
        .one()
    )

    with db.session.begin_nested():
        site_type_nom = create_nomenclature(
            nomenclature_type=site_type,
            cd_nomenclature="MODULE_1",
            label_default="test_site",
            label_fr="Site Test",
        )
        site_type_nom.active = True
        db.session.add(site_type_nom)
    return site_type_nom


@pytest.fixture(scope="function")
def site(module, site_type):
    with db.session.begin_nested():
        b_site = TMonitoringSites(
            base_site_name="test_site",
            geom=to_wkt(point["geometry"]),
            id_module=module.id_module,
            id_nomenclature_type_site=site_type.id_nomenclature,
        )
        # module.sites.append(b_site)
        b_site.modules.append(module)
        db.session.add(b_site)
    return b_site


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
def mail():
    pass


@pytest.fixture(scope="function")
def review_state():
    pass


@pytest.fixture(scope="function")
def my_config():
    return get_config()


@pytest.fixture(scope="function")
def attachment():
    return ""
