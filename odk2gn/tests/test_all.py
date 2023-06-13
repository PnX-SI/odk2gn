import pytest, csv, sys

from odk2gn.tests.fixtures import (
    submissions,
    datasets,
    header,
    data,
    taxon_and_list,
    module,
    point,
    module,
    nomenclature,
    observers_and_list,
    test,
    the_csv,
)
from odk2gn.tests.fixtures import site
from odk2gn.gn2_utils import (
    get_jdd_list,
    to_csv,
    get_site_list,
    get_taxon_list,
    get_observer_list,
    get_nomenclature_data,
    get_ref_nomenclature_list,
)
from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import to_wkt

# from odk2gn.odk_api import dummy

from pypnusershub.db.models import UserList, User

from geonature.utils.env import db


@pytest.mark.usefixtures()
class TestCommand:
    def test_synchronize_monitoring(self, mocker, submissions):
        from odk2gn.main import dummy

        mocker.patch("odk2gn.main.get_submissions", return_value=submissions)

        # la vrai fonction a "mocker" est synchronize_monitoring et non 'dummy'
        submissions = dummy()
        assert isinstance(submissions, list)

    """def test_upgrade_odk_form_monitoring(self, mocker):
      assert """


@pytest.mark.usefixtures("temporary_transaction")
class TestUtilsFunctions:
    def test_get_jdd_list1(self, datasets):
        ds = get_jdd_list(datasets)
        print(ds)
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
        assert r_data == data

    def test_get_taxon_list1(self, taxon_and_list):
        taxons = get_taxon_list(taxon_and_list["tax_list"].id_liste)
        print(taxons)
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

    def test_get_site_list1(self, module):
        sites = get_site_list(module.id_module)
        assert type(sites) is list
        dict_cols = set(sites[0].keys())
        assert set(["id_base_site", "base_site_name", "geometry"]).issubset(dict_cols)

    def test_get_nomenclature_list1(self, nomenclature):
        nomenclatures = get_ref_nomenclature_list(code_nomenclature_type="TEST")
        assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in nomenclatures]
        assert type(nomenclatures) is list
        dict_cols = set(nomenclatures[0].keys())
        assert set(
            ["code_nomenclature_type", "id_nomenclature", "cd_nomenclature", "label_default"]
        ).issubset(dict_cols)
        assert nomenclatures[0]["code_nomenclature_type"] == "TEST"
        noms2 = get_ref_nomenclature_list(code_nomenclature_type="TEST", cd_nomenclatures=["test"])
        print(noms2)
        assert nomenclature.id_nomenclature in [nom["id_nomenclature"] for nom in noms2]
        assert type(noms2) is list
        dict_cols = set(noms2[0].keys())
        assert set(
            ["code_nomenclature_type", "id_nomenclature", "cd_nomenclature", "label_default"]
        ).issubset(dict_cols)

    def test_bidule(self, test):
        user = db.session.query(User).filter_by(identifiant="bidule").one()
        print(user)

    # def test_bidule2(test):
    #     user = db.session.query(UserList).filter_by(identifiant="bidule").one()
    #     print(user)

    def test_csv_bis(self, taxon_and_list):
        taxons = get_taxon_list(taxon_and_list["tax_list"].id_liste)
        res = to_csv(["cd_nom", "nom_vern"], taxons)
        assert type(res) is str
