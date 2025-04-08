import pytest, csv
import flatdict

from sqlalchemy.orm.exc import NoResultFound
from gn_module_monitoring.monitoring.models import TMonitoringSites
from odk2gn.tests.fixtures import *
from odk2gn.odk_api import ODKSchema

from odk2gn.gn2_utils import (
    format_jdd_list,
    to_csv,
    get_taxon_list,
    get_observer_list,
    get_ref_nomenclature_list,
    get_module_code,
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
        mocker,
        sub_with_site_creation,
        mon_schema_fields,
        module,
        my_config,
        site_type,
        observers_and_list,
    ):
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=sub_with_site_creation)
        mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=mon_schema_fields)
        mocker.patch("odk2gn.monitoring.command.get_config", return_value=my_config)
        mocker.patch("odk2gn.monitoring.utils.get_attachment", return_value=b"")
        mocker.patch("odk2gn.gn2_utils.update_review_state", return_value={})
        mocker.patch(
            "odk2gn.gn2_utils.get_observers",
            return_value=observers_and_list["user_list"],
        )
        synchronize_module(module.module_code, 99, "bidon")

        assert True

    def test_failing_synchronize(
        self,
        mocker,
        failing_sub,
        mon_schema_fields,
        module,
        my_config,
        site_type,
        observers_and_list,
    ):
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=failing_sub)
        mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=mon_schema_fields)
        mocker.patch("odk2gn.monitoring.command.get_config", return_value=my_config)
        mocker.patch("odk2gn.monitoring.utils.get_attachment", return_value=b"")
        mocker.patch("odk2gn.gn2_utils.update_review_state", return_value={})
        mocker.patch(
            "odk2gn.gn2_utils.get_observers",
            return_value=observers_and_list["user_list"],
        )
        with pytest.raises(Exception):
            synchronize_module(module.module_code, 99, "bidon")


    def test_failing_synchronize_2(
        self,
        mocker,
        other_failing_sub,
        mon_schema_fields,
        module,
        my_config,
        site_type,
        observers_and_list,
    ):
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=other_failing_sub)
        mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=mon_schema_fields)
        mocker.patch("odk2gn.monitoring.command.get_config", return_value=my_config)
        mocker.patch("odk2gn.monitoring.utils.get_attachment", return_value=b"")
        mocker.patch("odk2gn.gn2_utils.update_review_state", return_value={})
        mocker.patch(
            "odk2gn.gn2_utils.get_observers",
            return_value=observers_and_list["user_list"],
        )
        with pytest.raises(AssertionError):
            synchronize_module(module.module_code, 99, "bidon")

    def test_failing_sync_3(
        self,
        mocker,
        failing_sub_3,
        mon_schema_fields,
        module,
        my_config,
        site_type,
        observers_and_list,
    ):
        """ 
            Fail because use 'failing_sub_3' fixture 
                -> dataset is None and no dataset is define a dataset level"

        """
        mocker.patch("odk2gn.monitoring.command.get_submissions", return_value=failing_sub_3)
        mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=mon_schema_fields)
        mocker.patch("odk2gn.monitoring.command.get_config", return_value=my_config)
        mocker.patch("odk2gn.monitoring.utils.get_attachment", return_value=b"")
        mocker.patch("odk2gn.gn2_utils.update_review_state", return_value={})
        mocker.patch(
            "odk2gn.gn2_utils.get_observers",
            return_value=observers_and_list["user_list"],
        )
        with pytest.raises(AssertionError):
            synchronize_module(module.module_code, 99, "bidon")


    def test_upgrade(self, mocker, my_config, module):
        mocker.patch("odk2gn.monitoring.command.update_form_attachment", return_value=b"")
        mocker.patch("odk2gn.monitoring.command.get_config", return_value=my_config)

        upgrade_module(
            module.module_code, 
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

    def test_get_site_list1(self, module, site):
        sites = get_site_list(module.id_module)
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
        # noms3 = get_ref_nomenclature_list(
        #     code_nomenclature_type="TEST",
        #     cd_nomenclatures=["test"],
        #     regne="all",
        #     group2_inpn="all",
        # )
        # assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in noms3]
        # assert type(noms3) is list
        # dict_cols = set(noms3[0].keys())
        # assert set(["mnemonique", "id_nomenclature", "cd_nomenclature", "label_default"]).issubset(
        #     dict_cols
        # )

    def test_get_modules_info1(self, module):
        mod = get_modules_info(module.module_code)
        assert mod == module

    def test_get_modules_info_error(self):
        try:
            get_modules_info(module_code="error")
        except NoResultFound:
            assert True

    # def test_bidule2(test):
    #     user = db.session.query(UserList).filter_by(identifiant="bidule").one()
    #     print(user)

    def test_monitoring_files(self, mocker, my_config, module):
        mocker.patch(
            "odk2gn.monitoring.utils.get_config",
            return_value=my_config,
        )
        files = get_gn2_attachments_data(module)
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

    def test_get_monitoring_config(self, mocker, my_config, module):
        mocker.patch(
            "odk2gn.monitoring.utils.get_config",
            return_value=my_config,
        )
        for niveau in ["site", "visit", "observation"]:
            nom_fields = get_nomenclatures_fields(module.module_code, niveau)
            assert type(nom_fields) is list

    def test_get_module_code(self, module):
        code = get_module_code(module.id_module)
        assert module.module_code == code

    def test_parse_and_create_site(
        self, mocker, sub_with_site_creation, mod_parser_config, my_config, module, site_type,
        mon_schema_fields
    ):
        for sub in sub_with_site_creation:
            flat_sub = flatdict.FlatDict(sub, delimiter="/")
            mocker.patch("odk2gn.odk_api.ODKSchema._get_schema_fields", return_value=mon_schema_fields)

            odk_schema = ODKSchema("test", "test")

            site = parse_and_create_site(flat_sub, mod_parser_config, my_config, module, odk_schema)
            assert type(site) is TMonitoringSites
            #TODO : improve check of site
