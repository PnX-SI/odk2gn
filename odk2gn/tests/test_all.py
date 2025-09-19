import pytest, csv

from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound
from gn_module_monitoring.monitoring.models import TMonitoringSites, TMonitoringVisits, TMonitoringObservations
from geonature.utils.env import db
from odk2gn.tests.fixtures import *
from odk2gn.odk_api import ODKSchema

from odk2gn.gn2_utils import (
    format_jdd_list,
    to_csv,
    get_taxon_list,
    get_observer_list,
    get_ref_nomenclature_list,
    get_module_code,
    flat_and_short_dict
    
)
from odk2gn.monitoring.utils import (
    parse_and_create_site,
    get_gn2_attachments_data,
    get_modules_info,
    get_site_list,
    get_nomenclatures_fields,
)


from odk2gn.monitoring.utils import get_modules_info

from odk2gn.monitoring.command import synchronize_module, upgrade_module

@pytest.mark.usefixtures("temporary_transaction")
class TestCommand:
    def test_synchronize_monitoring_site_creation(
        self,
        sub_with_site_creation,
        mocker,
        modules,
        site_type,
        sync_mocker,
        taxon_and_list
    ):
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=sub_with_site_creation)
        synchronize_module(modules["module_with_site"].module_code, 99, "bidon")
        created_site = db.session.execute(
            select(TMonitoringSites).filter_by(
                base_site_name=sub_with_site_creation[0]["site_creation"]["base_site_name"]
                )
        ).scalar_one()
        # test champs génériques
        assert created_site.base_site_description == sub_with_site_creation[0]["site_creation"]["base_site_description"]
        # test champs spécifiques
        assert "is_new" in created_site.data and created_site.data["is_new"] == True

        # test visite
        created_visit = db.session.execute(
            select(TMonitoringVisits).filter_by(
                id_base_site=created_site.id_base_site
                )
        ).unique().scalar_one()
        assert created_visit.comments == sub_with_site_creation[0]["visit"]["comments_visit"]
        assert "hauteur_moy_vegetation" in created_visit.data 
        assert created_visit.data["hauteur_moy_vegetation"] == sub_with_site_creation[0]["visit"]["hauteur_moy_vegetation"]

        # test observation
        created_obs = db.session.scalars(
            select(TMonitoringObservations).filter_by(
                id_base_visit=created_visit.id_base_visit
                )
        ).unique().all()

        assert len(created_obs) > 0
        first_obs = created_obs[0]
        assert first_obs.cd_nom == taxon_and_list["taxon"].cd_nom
        assert "addi" in first_obs.data
        assert first_obs.data["addi"] == "YES"


    def test_synchronize_with_only_visit_and_obs(
        self,
        submissions_with_no_site,
        modules,
        site_type,
        sync_mocker,
        mocker
    ):
        # ce test utilise un module dont la config (tests.test_config.py) ne permet pas la création de site
        # can_create_site = False
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=submissions_with_no_site)
        synchronize_module(modules["module_with_no_site"].module_code, 99, "bidon")

    def test_synchronize_with_only_visit_and_obs_in_creatable_site_module(
        self,
        submission_with_no_site_in_creatable_site_module,
        modules,
        site_type,
        sync_mocker,
        mocker
    ):
        # On utilise un module ou on peut créer des site mais ou on a choisi d'en selectionné un existant
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=submission_with_no_site_in_creatable_site_module)
        synchronize_module(modules["module_with_site"].module_code, 99, "bidon")

    def test_synchronize_with_only_visit(
        self,
        submissions_with_only_visit,
        modules,
        site_type,
        sync_mocker,
        mocker
    ):
        # ce test utilise un module dont la config (tests.test_config.py) ne permet pas la création de site
        # can_create_site = False
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=submissions_with_only_visit)
        synchronize_module(modules["module_with_no_site"].module_code, 99, "bidon")


    def test_failing_synchronize(
        self,
        mocker,
        failing_sub,
        modules,
        site_type,
        sync_mocker
    ):
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=failing_sub)
        with pytest.raises(Exception):
            synchronize_module(modules["module_with_site"].module_code, 99, "bidon")


    def test_failing_synchronize_2(
        self,
        mocker,
        other_failing_sub,
        modules,
        site_type,
        sync_mocker
    ):
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=other_failing_sub)

        with pytest.raises(AssertionError):
            synchronize_module(modules["module_with_site"].module_code, 99, "bidon")

    def test_failing_sync_3(
        self,
        mocker,
        failing_sub_3,
        modules,
        site_type,
        sync_mocker
    ):
        """ 
            Fail because use 'failing_sub_3' fixture 
                -> dataset is None and no dataset is define a dataset level"

        """
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=failing_sub_3)

        with pytest.raises(AssertionError):
            synchronize_module(modules["module_with_site"].module_code, 99, "bidon")


    def test_upgrade(self, mocker, my_config, modules):
        mocker.patch("odk2gn.monitoring.command.update_form_attachment", return_value=b"")
        mocker.patch("odk2gn.monitoring.utils.get_config", return_value=my_config)

        upgrade_module(
            modules["module_with_site"].module_code, 
            99, 
            "bidon"
            )
        
    def test_upgrade_no_observation(self, mocker, my_config_no_observation, modules):
        # test que l'upgrade fonctionne meme avec un module sans le niveau "observation"
        mocker.patch("odk2gn.monitoring.command.update_form_attachment", return_value=b"")
        mocker.patch("odk2gn.monitoring.utils.get_config", return_value=my_config_no_observation)

        upgrade_module(
            modules["module_with_site"].module_code, 
            99, 
            "bidon"
            )



@pytest.mark.usefixtures("temporary_transaction")
class TestUtilsFunctions:
    def test_format_jdd_list1(self, datasets):
        ds = format_jdd_list(datasets.values())

        assert type(ds) is list
        dict_cols = set(ds[0].keys())
        assert set(["id_dataset", "dataset_name"]).issubset(dict_cols)

    def test_to_csv1(self, header, data):
        content = to_csv(header, data).split("\n")

        reader = csv.reader(content)
        assert header == reader.__next__()
        r_data = []
        for row in reader:
            r_data.append(row)

        assert r_data == [["1", "2"], ["3", "4"], []]

    def test_get_taxon_list1(self, taxon_and_list):
        taxons = get_taxon_list(taxon_and_list["tax_list"].id_liste)
        # autre chose)
        # assert taxon_and_list["taxon"].cd_nom in [t[0] for t in taxons]
        assert type(taxons) is list
        dict_cols = set(taxons[0].keys())
        assert set(["cd_nom", "nom_vern", "nom_complet"]).issubset(dict_cols)

    def test_get_observer_list1(self, observers_and_list):
        observers = get_observer_list(observers_and_list["list"].id_liste)
        assert type(observers) is list
        dict_cols = set(observers[0].keys())
        assert set(["id_role", "nom_complet"]).issubset(dict_cols)

    def test_get_site_list1(self, modules, site):
        sites = get_site_list(modules["module_with_site"].id_module)
        assert type(sites) is list
        dict_cols = set(sites[0].keys())
        assert set(["id_base_site", "base_site_name", "geometry"]).issubset(dict_cols)

    def test_get_nomenclature_list1(self, nomenclature):
        nomenclatures = get_ref_nomenclature_list(code_nomenclature_type="TEST")
        assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in nomenclatures]
        assert type(nomenclatures) is list
        dict_cols = set(nomenclatures[0].keys())
        assert set(["mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"]).issubset(
            dict_cols
        )
        assert nomenclatures[0]["mnemonique"] == "TEST"
        noms2 = get_ref_nomenclature_list(code_nomenclature_type="TEST", cd_nomenclatures=["test"])
        assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in noms2]
        assert type(noms2) is list
        dict_cols = set(noms2[0].keys())
        assert set(["mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"]).issubset(
            dict_cols
        )

    def test_get_modules_info1(self, modules):
        mod = get_modules_info(modules["module_with_site"].module_code)
        assert mod == modules["module_with_site"]

    def test_get_modules_info_error(self):
        try:
            get_modules_info(module_code="error")
        except NoResultFound:
            assert True

    def test_monitoring_files(self, mocker, my_config, modules):
        mocker.patch(
            "odk2gn.monitoring.utils.get_config",
            return_value=my_config,
        )
        files = get_gn2_attachments_data(modules["module_with_site"])
        assert type(files) is dict
        files_names = set(files.keys())
        assert set(
            [
                "gn_jdds.csv",
                "gn_nomenclatures.csv",
                "gn_observateurs.csv",
                "gn_sites.csv",
                "gn_taxons.csv",
                "gn_groupes.csv",
            ]
        ).issubset(files_names)

    def test_get_monitoring_config(self, mocker, my_config, modules):
        mocker.patch(
            "odk2gn.monitoring.utils.get_config",
            return_value=my_config,
        )
        for niveau in ["site", "visit", "observation"]:
            nom_fields = get_nomenclatures_fields(modules["module_with_site"].module_code, niveau)
            assert type(nom_fields) is list

    def test_get_module_code(self, modules):
        code = get_module_code(modules["module_with_site"].id_module)
        assert modules["module_with_site"].module_code == code

    def test_parse_and_create_site(
        self, mocker, sub_with_site_creation, mod_parser_config, my_config, modules, site_type,
    ):
        for sub in sub_with_site_creation:
            flat_sub = flat_and_short_dict(sub)
            mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=odk_field_schema)

            odk_schema = ODKSchema("test", "test")

            site = parse_and_create_site(flat_sub, mod_parser_config, my_config, modules, odk_schema)
            assert type(site) is TMonitoringSites


    def test_flat_and_short(self, dict_to_flat_and_short):
        res = flat_and_short_dict(dict_to_flat_and_short)
        assert "coords" in res
        assert "type" in res