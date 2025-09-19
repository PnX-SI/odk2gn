import pytest
import csv
import uuid
import datetime
import copy
from pathlib import Path
from odk2gn.gn2_utils import to_wkb
from geonature.utils.env import db
from pypnusershub.db.models import UserList, User
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes, CorTaxrefNomenclature
from geonature.tests.fixtures import *
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringSites,
    TMonitoringSitesGroups,
    BibTypeSite,
)
from apptax.taxonomie.models import BibListes, Taxref


@pytest.fixture(scope="function")
def point():
    point = {"geometry": {"type": "Point", "coordinates": [6.0535113, 44.5754145]}}
    return point



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
def site_group(modules):
    with db.session.begin_nested():
        group = TMonitoringSitesGroups(
            modules=[modules["module_with_site"]],
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
        taxon_test_list = BibListes(code_liste="test_list", nom_liste="Liste test")
        taxon.listes.append(taxon_test_list)
        db.session.add(taxon, taxon_test_list)
    return {"taxon": taxon, "tax_list": taxon_test_list}


@pytest.fixture(scope="function")
def modules(site_type):
    def create_module(module_name):
        with db.session.begin_nested():
            new_module = TMonitoringModules(
                module_code=module_name,
                module_label=module_name,
                module_path=module_name,
                active_frontend=True,
                active_backend=False,
                types_site=[site_type],
            )
            db.session.add(new_module)
            db.session.flush()
            return new_module

    return {
        "module_with_site": create_module("module_with_site"),
        "module_with_no_site": create_module("module_with_no_site"),
    }




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
        site_type = BibTypeSite(nomenclature=site_type_nom, config=None)
        db.session.add(site_type_nom, site_type)
    return site_type


@pytest.fixture(scope="function")
def site(modules, site_type, point):
    with db.session.begin_nested():
        b_site = TMonitoringSites(
            base_site_name="test_site", geom=to_wkb(point["geometry"]), types_site=[site_type]
        )
        b_site.modules.append(modules["module_with_no_site"])
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


#mon_schema_fields

odk_field_schema =  [
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
        {
            "path": "/is_new",
            "name": "is_new",
            "type": "boolean",
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
            "path": "/visit_point/hauteur_moy_vegetation",
            "name": "hauteur_moy_vegetation",
            "type": "int",
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
            "path": "/types_site",
            "name": "types_site",
            "type": "string",
            "binary": None,
            "selectMultiple": True,
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
            "path": "/is_new",
            "name": "is_new",
            "type": "boolean",
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
            "path": "/observations/addi",
            "name": "addi",
            "type": "string",
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
        {
            "path": "/meta/nb_observations",
            "name": "nb_observations",
            "type": "number",
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
def sub_with_site_creation(
    observers_and_list,
    modules,
    taxon_and_list,
    site_group,
    site_type,
    polygon_4,
    point,
    nomenclature,
    datasets
):
    __id = str(uuid.uuid4())
    sub = [
        {
            "__id": __id,
            "create_site": "true",
            "id_digitiser": observers_and_list["user_list"][0].id_role,
            "site_creation": {
                "base_site_name": "test de creation de site",
                "base_site_description": "test",
                "geom": point["geometry"],
                "type": "Point",
                # is_new est un champ additionnel
                "is_new": True,
                "site_group": site_group.id_sites_group,
                # tel que renvoyé par l'API 'types_site' est une chaine de
                # charactère avec des id_type_site séparé par des espaces
                "types_site": str(site_type.id_nomenclature_type_site),
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": modules["module_with_site"].id_module,
                "media": b"",
                "media_type": "Photo",
                "comments_visit": "test",
                "dataset": {"id_dataset": datasets["own_dataset"].id_dataset},
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
                    "comments": "test sub_with_site_creation",
                    "addi" : "YES"
                }
            ],
            "meta": {"instanceID": "uuid:" + __id},
        },
        {
            "__id": str(uuid.uuid4()),
            "create_site": "true",
            "site_creation": {
                "base_site_name": "test",
                "base_site_description": "test",
                "geom": polygon_4["geometry"],
                "types_site": str(site_type.id_nomenclature_type_site),
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": modules["module_with_site"].id_module,
                "medias_visit": "images/pictos/nopicto.gif",
                "comments_visit": "test",
                "dataset": {"id_dataset": datasets["own_dataset"].id_dataset},
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
def submissions_with_no_site(site, observers_and_list, modules, taxon_and_list):
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "id_digitiser": observers_and_list["user_list"][0].id_role,
            "id_base_site": site.id_base_site,
            "base_site_name": site.base_site_name,
            "visit": {
                "visit_date_min": str(datetime.date.today()),
                "id_module": modules["module_with_no_site"].id_module,
                "comments": "test",
                "observers": [{"id_role": observers_and_list["user_list"][0].id_role}],
                "hauteur_moy_vegetation": 12,
            },
            "dataset": {"id_dataset": 1},
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": 1,
                    "comments": "test submission",
                }
            ],
        },
    ]
    return sub

@pytest.fixture(scope="function")
def submission_with_no_site_in_creatable_site_module(submissions_with_no_site):
    """
    Soumissions sans site dans un site ou on peut créer des sites
    """
    new_subs = []
    submissions_with_no_site_copy = copy.deepcopy(submissions_with_no_site)
    for sub in submissions_with_no_site_copy:
        sub["create_site"] = False
        new_subs.append(sub)
    return new_subs
        

@pytest.fixture(scope="function")
def submissions_with_only_visit(submissions_with_no_site):
    subs = []
    for sub in submissions_with_no_site:
        sub.pop("observations")
        subs.append(sub)
    return subs

@pytest.fixture(scope="function")
def submissions_with_only_site(sub_with_site_creation):
    subs = []
    for sub in sub_with_site_creation:
        sub.pop("visit")
        subs.append(sub)
    return subs



@pytest.fixture(scope="function")
def failing_sub(observers_and_list, modules, site_type, taxon_and_list, site_group, point):
    "Fail because dataset does not exists"
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "id_digitiser": observers_and_list["user_list"][0].id_role,
            "create_site": "true",
            "site_creation": {
                "base_site_name": "test",
                "base_site_description": "test",
                "geom": point["geometry"],
                "is_new": True,
                "site_group": site_group.id_sites_group,
                "types_site": str(site_type.id_nomenclature_type_site),
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": modules["module_with_site"].id_module,
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
            "dataset": {"id_dataset": 152111},
            "nb_observations": 1,
            "observations": [
                {
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": 1,
                    "comments_observation": "test failing sub",
                    "medias_observation": None,
                }
            ],
        },
    ]
    return sub


@pytest.fixture(scope="function")
def other_failing_sub(observers_and_list, modules, taxon_and_list, site_group, point, datasets):
    "Fail because observation is not a list"
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "create_site": "true",
            "id_digitiser": observers_and_list["user_list"][0].id_role,
            "site_creation": {
                "base_site_name": "test",
                "base_site_description": "test",
                "geom": point["geometry"],
                "is_new": True,
                "site_group": site_group.id_sites_group,
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": modules["module_with_site"].id_module,
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
            "dataset": {"id_dataset": datasets["own_dataset"].id_dataset},
            "nb_observations": 1,
            "observations": ({
                    "cd_nom": taxon_and_list["taxon"].cd_nom,
                    "comptage": "1",
                    "comments_observation": "test other failing sub",
                    "medias_observation": None,
                    "id_digitiser": observers_and_list["user_list"][0].id_role,
            },),
        },
    ]
    return sub


@pytest.fixture(scope="function")
def failing_sub_3(observers_and_list, modules, taxon_and_list, site_group, point):
    "Fail because dataset is None and no dataset is define a dataset level"
    sub = [
        {
            "__id": str(uuid.uuid4()),
            "create_site": "true",
            "id_digitiser": observers_and_list["user_list"][0].id_role,
            "site_creation": {
                "base_site_name": "test",
                "base_site_description": "test",
                "geom": point["geometry"],
                "is_new": True,
                "site_group": site_group.id_sites_group,
            },
            "visit": {
                "visit_date_min": str(datetime.datetime.now()),
                "id_module": modules["module_with_site"].id_module,
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
                    "comments_observation": "test failing sub 3",
                    "medias_observation": None,
                    "id_digitiser": observers_and_list["user_list"][0].id_role,
                }
            ],
        },
    ]
    return sub


@pytest.fixture(scope="function")
def mod_parser_config(modules):
    conf = {
        "module_code": modules["module_with_site"].module_code,
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
def my_config(modules, site_type, nomenclature):
    conf = {
        "module": {
            "module_label": modules["module_with_site"].module_code,
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
                "id_nomenclature_type_site": {
                    "attribut_label": "Type site",
                    "code_nomenclature_type": "TYPE_SITE",
                    "hidden": True,
                    "required": True,
                    "type_util": "nomenclature",
                    "type_widget": "nomenclature",
                    "value": {
                        "cd_nomenclature": "STOM",
                        "code_nomenclature_type": "TYPE_SITE"
                    }
                }
            },
            "specific": {
                "id_nomenclature_type_site": {
                    "hidden": True,
                    "value": {
                        "code_nomenclature_type": "TYPE_SITE",
                        "cd_nomenclature": site_type.nomenclature.cd_nomenclature,
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
                "nb_observations": {"attribut_label": "Nombre d'observations"},
                "hauteur_moy_vegetation": {"attribut_label": "Hauteur moyenne"}
            },
            "children_types": ["observation"],
            "parent_types": ["site"],
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
            "specific": {
                "addi" : {"attribut_label": "Commentaires",}
            },
            "children_types": [],
            "parent_types": ["visit"],
        },
    }
    return conf

@pytest.fixture(scope="function")
def my_config_no_observation(my_config):
    new_config = my_config.copy()
    new_config.pop("observation")
    return new_config


@pytest.fixture(scope="function")
def dict_to_flat_and_short():
    return {
        "group": {
                "sites_group": {
                    "geom": {
                        "coords": 123,
                        "type": "Point"
                    }
                }
        }
    }


@pytest.fixture(scope="function")
def sync_mocker(mocker, my_config, observers_and_list):
    mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=odk_field_schema)
    mocker.patch("odk2gn.monitoring.command.get_config", return_value=my_config)
    mocker.patch("odk2gn.monitoring.utils.get_attachment", return_value=b"")
    mocker.patch("odk2gn.gn2_utils.update_review_state", return_value={})
    mocker.patch(
        "odk2gn.gn2_utils.get_observers",
        return_value=observers_and_list["user_list"],
    )
