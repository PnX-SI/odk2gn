import pytest
import csv
import os
import uuid
import datetime
import flatdict
import json
from pathlib import Path
from odk2gn.gn2_utils import to_wkb
from geonature.utils.env import db
from geonature import create_app
from geonature.core.gn_meta.models import TDatasets
from sqlalchemy.event import listen, remove
from geonature.core.gn_commons.models import TModules
from gn_module_monitoring.config.repositories import get_config
from pypnusershub.db.models import UserList, User
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature
from geonature.core.gn_monitoring.models import TBaseSites, corSiteModule
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringSitesGroups,
)
from apptax.taxonomie.models import BibListes, Taxref
from utils_flask_sqla.tests.utils import JSONClient


@pytest.fixture(scope="function")
def point():
    point = {"geometry": {"type": "Point", "coordinates": [6.0535113, 44.5754145]}}
    return point


@pytest.fixture(scope="function")
def point_4():
    point = {"geometry": {"type": "Point", "coordinates": [6.0535113, 44.5754145, 0, 0]}}
    return point


@pytest.fixture(scope="function")
def point_3():
    point = {"geometry": {"type": "Point", "coordinates": [6.0535113, 44.5754145, 0]}}
    return point


@pytest.fixture(scope="function")
def polygon():
    polygon = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [6.0535113, 44.5754145],
                    [6.0535109, 44.5754135],
                    [6.0535120, 44.5754150],
                    [6.0535113, 44.5754145],
                ],
            ],
        }
    }
    return polygon


@pytest.fixture(scope="function")
def polygon_4():
    polygon = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [6.0535113, 44.5754145, 0, 0],
                    [6.0535109, 44.5754135, 0, 0],
                    [6.0535120, 44.5754150, 0, 0],
                    [6.0535113, 44.5754145, 0, 0],
                ],
            ],
        }
    }
    return polygon


@pytest.fixture(scope="function")
def polygon_3():
    polygon = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [6.0535113, 44.5754145, 0],
                    [6.0535109, 44.5754135, 0],
                    [6.0535120, 44.5754150, 0],
                    [6.0535113, 44.5754145, 0],
                ],
            ],
        }
    }
    return polygon


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
        taxon_test_list = BibListes(code_liste="test_list", nom_liste="Liste test", picto=picto)
        taxon_and_list.noms.append(taxon)
        db.session.add(taxon_test_list)
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
        ctrn = CorTaxrefNomenclature(
            id_nomenclature=nomenclature.id_nomenclature, regne="all", group2_inpn="all"
        )
        db.session.add(nomenclature, ctrn)
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
def site(module, site_type, point):
    with db.session.begin_nested():
        b_site = TMonitoringSites(
            base_site_name="test_site",
            geom=to_wkb(point["geometry"]),
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
def attachment():
    file = Path("/home/geonature/geonature/odk2gn/docs/img/archi_global.jpeg")
    return file


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
def sub_with_site_creation(
    observers_and_list,
    module,
    taxon_and_list,
    site_group,
    polygon,
    polygon_4,
    point,
    point_4,
    point_3,
    polygon_3,
    nomenclature,
    attachment,
):
    __id = str(uuid.uuid4())
    sub = [
        {
            "__id": __id,
            "create_site": "true",
            "site_creation": {
                "site_name": "test",
                "base_site_description": "test",
                "geom": point_4["geometry"],
                "is_new": True,
                "site_group": site_group.id_sites_group,
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": module.id_module,
                "media": attachment,
                "media_type": "Photo",
                "comments_visit": "test",
                "dataset": {"id_dataset": 1},
                "observers": [
                    {
                        "observer": observers_and_list["user_list"][0],
                        "id_role": observers_and_list["user_list"][0].id_role,
                    }
                ],
                "hauteur_moy_vegetation": 12,
                "nb_observations": 1,
                "test_nomenclature": nomenclature,
                "datalist": {
                    "params": {"regne": "all", "group2_inpn": "all"},
                },
            },
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comments": "test",
                }
            ],
            "meta": {"instanceID": "uuid:" + __id},
        },
        {
            "__id": str(uuid.uuid4()),
            "create_site": "true",
            "site_creation": {
                "site_name": "test",
                "base_site_description": "test",
                "geom": polygon_4["geometry"],
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": module.id_module,
                "medias_visit": "images/pictos/nopicto.gif",
                "comments_visit": "test",
                "dataset": {"id_dataset": 1},
                "observers": [
                    {
                        "observer": observers_and_list["user_list"][0],
                        "id_role": observers_and_list["user_list"][0].id_role,
                    }
                ],
                "hauteur_moy_vegetation": 12,
                "nb_observations": 0,
            },
        },
    ]
    return sub


@pytest.fixture(scope="function")
def failing_sub(observers_and_list, module, taxon_and_list, site_group, point):
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
                "medias_visit": None,
                "comments_visit": "test",
                "observers": [
                    {
                        "observer": observers_and_list["user_list"][0],
                        "id_role": observers_and_list["user_list"][0].id_role,
                    }
                ],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": 100},
            "nb_observations": 1,
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": 1,
                    "comments_observation": "test",
                    "medias_observation": None,
                }
            ],
        },
    ]
    return sub


@pytest.fixture(scope="function")
def other_failing_sub(observers_and_list, module, taxon_and_list, site_group, point):
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
                "medias_visit": None,
                "comments_visit": "test",
                "observers": [
                    {
                        "observer": observers_and_list["user_list"][0],
                        "id_role": observers_and_list["user_list"][0].id_role,
                    }
                ],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": 1},
            "nb_observations": 1,
            "observations": (
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": "1",
                    "comments_observation": "test",
                    "medias_observation": None,
                }
            ),
        },
    ]
    return sub


@pytest.fixture(scope="function")
def failing_sub_3(observers_and_list, module, taxon_and_list, site_group, point):
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
                "medias_visit": None,
                "comments_visit": "test",
                "observers": [
                    {
                        "observer": observers_and_list["user_list"][0],
                        "id_role": observers_and_list["user_list"][0].id_role,
                    }
                ],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": None},
            "nb_observations": 1,
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": 1,
                    "comments_observation": "test",
                    "medias_observation": None,
                }
            ],
        },
    ]
    return sub


@pytest.fixture(scope="function")
def mod_parser_config(module):
    conf = {
        "module_code": module.module_code,
        "SITE": {
            "base_site_name": "site_name",
            "base_site_description": "base_site_description",
            "geom": "geom",
            "first_use_date": "visit_date_min",
            "id_inventor": "observers",
            "data": "site_creation",
            "site_group": "site_group",
        },
        "VISIT": {"media": "media", "media_type": "media_type", "comments": "comments_visit"},
        "OBSERVATION": {
            "comments": "comments_observation",
            "media": "medias_observation",
            "comptage": "comptage",
        },
    }
    return conf


@pytest.fixture(scope="function")
def my_config(module, site_type, nomenclature):
    conf = {
        "module": {
            "module_label": module.module_code,
            "module_desc": "Test module",
            "children_types": ["site"],
            "parent_types": [],
        },
        "site": {
            "generic": {
                "id_base_site": {
                    "type_widget": "text",
                    "attribut_label": "Id site",
                    "hidden": True,
                },
                "id_module": {
                    "type_widget": "text",
                    "attribut_label": "ID Module",
                    "hidden": True,
                },
                "base_site_code": {
                    "type_widget": "text",
                    "attribut_label": "Code",
                    "required": True,
                },
                "base_site_name": {
                    "type_widget": "text",
                    "attribut_label": "Nom",
                    "required": True,
                },
                "base_site_description": {
                    "type_widget": "textarea",
                    "attribut_label": "Description",
                },
            },
            "specific": {
                "id_nomenclature_type_site": {
                    "hidden": True,
                    "value": {
                        "code_nomenclature_type": "TYPE_SITE",
                        "cd_nomenclature": site_type.cd_nomenclature,
                    },
                },
                "is_new": {"hidden": True, "type_widget": "bool_checkbox"},
            },
            "children_types": ["visit"],
            "parent_types": ["module"],
        },
        "visit": {
            "generic": {
                "id_base_visit": {
                    "type_widget": "text",
                    "attribut_label": "ID",
                    "hidden": True,
                },
                "id_base_site": {
                    "type_widget": "text",
                    "attribut_label": "ID SITE",
                    "hidden": True,
                },
                "id_module": {
                    "type_widget": "text",
                    "attribut_label": "ID Module",
                    "hidden": True,
                },
                "observers": {
                    "type_widget": "datalist",
                    "attribut_label": "Observateurs",
                    "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
                    "application": "GeoNature",
                    "keyValue": "id_role",
                    "keyLabel": "nom_complet",
                    "type_util": "user",
                    "multiple": True,
                    "required": True,
                },
                "id_digitiser": {
                    "type_widget": "text",
                    "attribut_label": "Digitiser",
                    "type_util": "user",
                    "required": True,
                    "hidden": True,
                },
                "visit_date_min": {
                    "type_widget": "date",
                    "attribut_label": "Date",
                    "required": True,
                },
                "visit_date_max": {
                    "type_widget": "date",
                    "attribut_label": "Date (max)",
                    "hidden": True,
                },
                "comments": {"type_widget": "text", "attribut_label": "Commentaires"},
                "uuid_base_visit": {"attribut_label": "uuid"},
                "id_dataset": {
                    "type_widget": "dataset",
                    "type_util": "dataset",
                    "attribut_label": "Jeu de données",
                    "module_code": "__MODULE.MODULE_CODE",
                    "required": True,
                },
                "nb_observations": {"attribut_label": "Nombre d'observations"},
                "medias": {
                    "type_widget": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_base_visits",
                },
            },
            "specific": {
                "dataset": {
                    "id_dataset": {
                        "hidden": True,
                        "required": True,
                    },
                },
                "nomenclature": {
                    "type_widget": "nomenclature",
                    "code_nomenclature_type": nomenclature.nomenclature_type.mnemonique,
                    "cd_nomenclature": nomenclature.cd_nomenclature,
                },
                "comments": {
                    "type_widget": "textarea",
                    "attribut_label": "Commentaire (autres indices, présence d'autres espèces, etc..)",
                },
                "medias": {
                    "hidden": True,
                    "type_widget": "medias",
                    "schema_dot_table": "gn_monitoring.t_base_visits",
                },
                "datalist": {
                    "type_widget": "datalist",
                    "type_util": "nomenclature",
                    "api": "nomenclatures/TEST",
                    "params": {"regne": "all", "group2_inpn": "all"},
                },
            },
            "children_types": ["observation"],
            "parent_types": ["site"],
            "nb_observations": {"attribut_label": "Nombre d'observations"},
        },
        "observation": {
            "generic": {
                "id_observation": {
                    "type_widget": "text",
                    "attribut_label": "Id observation",
                    "hidden": True,
                },
                "id_base_visit": {
                    "type_widget": "text",
                    "attribut_label": "Id visite",
                    "hidden": True,
                },
                "cd_nom": {
                    "type_widget": "taxonomy",
                    "attribut_label": "Espèce",
                    "type_util": "taxonomy",
                    "required": True,
                    "id_list": "__MODULE.ID_LIST_TAXONOMY",
                },
                "comments": {
                    "type_widget": "text",
                    "attribut_label": "Commentaires",
                },
                "uuid_observation": {"attribut_label": "uuid"},
                "medias": {
                    "type_widget": "medias",
                    "attribut_label": "Médias",
                    "schema_dot_table": "gn_monitoring.t_observations",
                },
            },
            "specific": {},
            "children_types": [],
            "parent_types": ["visit"],
        },
    }
    return conf


"======================================================================================================================================================================"

{
    "tree": {"module": {"site": {"visit": {"observation": None}}}},
    "synthese": "__MODULE.B_SYNTHESE",
    "default_display_field_names": {
        "user": "nom_complet",
        "nomenclature": "label_fr",
        "dataset": "dataset_name",
        "observer_list": "nom_liste",
        "taxonomy": "__MODULE.TAXONOMY_DISPLAY_FIELD_NAME",
        "taxonomy_list": "nom_liste",
        "sites_group": "sites_group_name",
        "habitat": "lb_hab_fr",
        "area": "area_name",
        "municipality": "nom_com_dept",
        "site": "base_site_name",
    },
    "module": {
        "cruved": {"C": 4, "U": 3, "D": 4},
        "id_field_name": "id_module",
        "description_field_name": "module_label",
        "label": "Module",
        "genre": "M",
        "uuid_field_name": "uuid_module_complement",
        "display_properties": ["module_label", "module_desc", "datasets"],
        "generic": {
            "id_module": {"type_widget": "text", "attribut_label": "ID", "hidden": True},
            "module_code": {
                "type_widget": "text",
                "attribut_label": "Code",
                "required": True,
                "hidden": True,
            },
            "module_label": {
                "type_widget": "text",
                "attribut_label": "Nom",
                "required": True,
                "hidden": True,
            },
            "module_path": {
                "type_widget": "text",
                "attribut_label": "Path",
                "required": True,
                "hidden": True,
            },
            "module_desc": {
                "type_widget": "text",
                "attribut_label": "Description",
                "required": True,
                "hidden": True,
            },
            "module_picto": {
                "type_widget": "text",
                "attribut_label": "Icone dans le menu",
                "required": True,
            },
            "uuid_module_complement": {"attribut_label": "uuid"},
            "datasets": {
                "type_widget": "dataset",
                "type_util": "dataset",
                "attribut_label": "Jeu de données",
                "required": True,
                "multi_select": True,
            },
            "id_list_observer": {
                "type_widget": "datalist",
                "attribut_label": "Liste des observateurs",
                "keyValue": "id_liste",
                "keyLabel": "nom_liste",
                "multiple": False,
                "api": "users/listes",
                "application": "GeoNature",
                "required": True,
                "type_util": "observer_list",
                "definition": "Liste des observateurs. À gérer dans UsersHub.",
            },
            "id_list_taxonomy": {
                "type_widget": "datalist",
                "attribut_label": "Liste des taxons",
                "keyValue": "id_liste",
                "keyLabel": "nom_liste",
                "multiple": False,
                "api": "biblistes/",
                "application": "TaxHub",
                "required": True,
                "type_util": "taxonomy_list",
                "data_path": "data",
                "definition": "Liste des taxons. À gérer dans TaxHub.",
            },
            "b_synthese": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Activer la synthèse ?",
                "definition": "Insertion automatique des nouvelles données dans la synthèse.",
            },
            "b_draw_sites_group": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Dessiner les groupes de sites",
                "definition": "Affichage des groupes de site en dessinant l'enveloppe des sites du groupe et en affichant l'aire du groupe de sites",
                "hidden": True,
            },
            "taxonomy_display_field_name": {
                "type_widget": "datalist",
                "attribut_label": "Affichage des taxons",
                "values": [
                    {"label": "Nom vernaculaire ou nom latin", "value": "nom_vern,lb_nom"},
                    {"label": "Nom latin", "value": "lb_nom"},
                ],
                "required": True,
            },
            "active_frontend": {
                "type_widget": "bool_checkbox",
                "attribut_label": "Afficher dans le menu ?",
                "definition": "Afficher le module dans le menu de GeoNature. (Recharger la page pour voir les modifications).",
            },
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_module_complements",
            },
        },
        "children_types": ["site"],
        "parent_types": [],
        "specific": {},
        "display_list": ["module_label", "module_desc", "datasets"],
        "properties_keys": [
            "id_module",
            "module_code",
            "module_label",
            "module_path",
            "module_desc",
            "module_picto",
            "uuid_module_complement",
            "datasets",
            "id_list_observer",
            "id_list_taxonomy",
            "b_synthese",
            "b_draw_sites_group",
            "taxonomy_display_field_name",
            "active_frontend",
            "medias",
        ],
        "display_form": [],
        "root_object": True,
        "id_table_location": 11,
        "filters": {},
    },
    "site": {
        "cruved": {"C": 1, "U": 1, "D": 1},
        "chained": True,
        "id_field_name": "id_base_site",
        "description_field_name": "base_site_name",
        "label": "Site",
        "genre": "M",
        "geom_field_name": "geom",
        "uuid_field_name": "uuid_base_site",
        "geometry_type": "Point",
        "display_properties": [
            "base_site_name",
            "base_site_code",
            "base_site_description",
            "id_nomenclature_type_site",
            "id_inventor",
            "first_use_date",
            "last_visit",
            "nb_visits",
            "altitude_min",
            "altitude_max",
        ],
        "display_list": [
            "base_site_name",
            "base_site_code",
            "id_nomenclature_type_site",
            "last_visit",
            "nb_visits",
        ],
        "sorts": [{"prop": "last_visit", "dir": "desc"}],
        "generic": {
            "id_base_site": {"type_widget": "text", "attribut_label": "Id site", "hidden": True},
            "id_module": {"type_widget": "text", "attribut_label": "ID Module", "hidden": True},
            "base_site_code": {"type_widget": "text", "attribut_label": "Code", "required": True},
            "base_site_name": {"type_widget": "text", "attribut_label": "Nom", "required": True},
            "base_site_description": {"type_widget": "textarea", "attribut_label": "Description"},
            "id_sites_group": {
                "type_widget": "datalist",
                "attribut_label": "Groupe de sites",
                "type_util": "sites_group",
                "keyValue": "id_sites_group",
                "keyLabel": "sites_group_name",
                "api": "__MONITORINGS_PATH/list/__MODULE.MODULE_CODE/sites_group?id_module=__MODULE.ID_MODULE&fields=id_sites_group&fields=sites_group_name",
                "application": "GeoNature",
                "required": False,
                "hidden": True,
            },
            "id_nomenclature_type_site": {
                "type_widget": "datalist",
                "attribut_label": "Type site",
                "api": "nomenclatures/nomenclature/TYPE_SITE",
                "application": "GeoNature",
                "keyValue": "id_nomenclature",
                "keyLabel": "label_fr",
                "data_path": "values",
                "type_util": "nomenclature",
                "required": True,
            },
            "id_inventor": {
                "type_widget": "datalist",
                "attribut_label": "Descripteur",
                "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
                "application": "GeoNature",
                "keyValue": "id_role",
                "keyLabel": "nom_complet",
                "type_util": "user",
                "required": True,
            },
            "id_digitiser": {
                "type_widget": "text",
                "attribut_label": "Numérisateur",
                "required": True,
                "hidden": True,
                "type_util": "user",
            },
            "first_use_date": {
                "type_widget": "date",
                "attribut_label": "Date description",
                "required": True,
            },
            "last_visit": {"attribut_label": "Dernière visite", "type_util": "date"},
            "nb_visits": {"attribut_label": "Nb. visites"},
            "uuid_base_site": {"attribut_label": "uuid"},
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_base_sites",
            },
            "altitude_min": {"type_widget": "integer", "attribut_label": "Altitude (min)"},
            "altitude_max": {"type_widget": "integer", "attribut_label": "Altitude (max)"},
        },
        "children_types": ["visit"],
        "parent_types": ["module"],
        "specific": {},
        "properties_keys": [
            "id_base_site",
            "id_module",
            "base_site_code",
            "base_site_name",
            "base_site_description",
            "id_sites_group",
            "id_nomenclature_type_site",
            "id_inventor",
            "id_digitiser",
            "first_use_date",
            "last_visit",
            "nb_visits",
            "uuid_base_site",
            "medias",
            "altitude_min",
            "altitude_max",
        ],
        "display_form": [],
        "id_table_location": 2,
        "filters": {},
    },
    "visit": {
        "cruved": {"C": 1, "U": 1, "D": 1},
        "id_field_name": "id_base_visit",
        "chained": True,
        "description_field_name": "visit_date_min",
        "label": "Visite",
        "genre": "F",
        "uuid_field_name": "uuid_base_visit",
        "display_properties": [
            "id_base_site",
            "visit_date_min",
            "observers",
            "comments",
            "dataset",
            "nb_observations",
        ],
        "display_list": [
            "id_base_site",
            "visit_date_min",
            "observers",
            "comments",
            "dataset",
            "nb_observations",
        ],
        "sorts": [{"prop": "visit_date_min", "dir": "desc"}],
        "generic": {
            "id_base_visit": {"type_widget": "text", "attribut_label": "ID", "hidden": True},
            "id_base_site": {"type_widget": "text", "attribut_label": "ID SITE", "hidden": True},
            "id_module": {"type_widget": "text", "attribut_label": "ID Module", "hidden": True},
            "observers": {
                "type_widget": "datalist",
                "attribut_label": "Observateurs",
                "api": "users/menu/__MODULE.ID_LIST_OBSERVER",
                "application": "GeoNature",
                "keyValue": "id_role",
                "keyLabel": "nom_complet",
                "type_util": "user",
                "multiple": True,
                "required": True,
            },
            "id_digitiser": {
                "type_widget": "text",
                "attribut_label": "Digitiser",
                "type_util": "user",
                "required": True,
                "hidden": True,
            },
            "visit_date_min": {"type_widget": "date", "attribut_label": "Date", "required": True},
            "visit_date_max": {
                "type_widget": "date",
                "attribut_label": "Date (max)",
                "hidden": True,
            },
            "comments": {"type_widget": "text", "attribut_label": "Commentaires"},
            "uuid_base_visit": {"attribut_label": "uuid"},
            "id_dataset": {
                "type_widget": "dataset",
                "type_util": "dataset",
                "attribut_label": "Jeu de données",
                "module_code": "__MODULE.MODULE_CODE",
                "required": True,
            },
            "nb_observations": {"attribut_label": "Nombre d'observations"},
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_base_visits",
            },
        },
        "children_types": ["observation"],
        "parent_types": ["site"],
        "specific": {},
        "properties_keys": [
            "id_base_visit",
            "id_base_site",
            "id_module",
            "observers",
            "id_digitiser",
            "visit_date_min",
            "visit_date_max",
            "comments",
            "uuid_base_visit",
            "id_dataset",
            "nb_observations",
            "medias",
        ],
        "display_form": [],
        "id_table_location": 3,
        "filters": {},
    },
    "observation": {
        "cruved": {"C": 1, "U": 1, "D": 1},
        "id_field_name": "id_observation",
        "description_field_name": "id_observation",
        "chained": True,
        "label": "Observation",
        "genre": "F",
        "display_properties": ["cd_nom", "comments"],
        "uuid_field_name": "uuid_observation",
        "generic": {
            "id_observation": {
                "type_widget": "text",
                "attribut_label": "Id observation",
                "hidden": True,
            },
            "id_base_visit": {
                "type_widget": "text",
                "attribut_label": "Id visite",
                "hidden": True,
            },
            "cd_nom": {
                "type_widget": "taxonomy",
                "attribut_label": "Espèce",
                "type_util": "taxonomy",
                "required": True,
                "id_list": "__MODULE.ID_LIST_TAXONOMY",
            },
            "comments": {"type_widget": "text", "attribut_label": "Commentaires"},
            "uuid_observation": {"attribut_label": "uuid"},
            "medias": {
                "type_widget": "medias",
                "attribut_label": "Médias",
                "schema_dot_table": "gn_monitoring.t_observations",
            },
        },
        "children_types": [],
        "parent_types": ["visit"],
        "specific": {},
        "display_list": ["cd_nom", "comments"],
        "properties_keys": [
            "id_observation",
            "id_base_visit",
            "cd_nom",
            "comments",
            "uuid_observation",
            "medias",
        ],
        "display_form": [],
        "id_table_location": 12,
        "filters": {},
    },
}
