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
        formated_ds = get_jdd_list(datasets)
        assert formated_ds == [[1, "ds1"], [2, "ds2"]]

    def test_to_csv1(self, header, data, the_csv):
        content = to_csv(header, data).split("\n")
        # load and lib csv
        with open("test.csv", "r") as file:
            reader = csv.reader(file)
            for c in content:
                c_line = c.split(",")
                r_line = reader.__next__()
                assert c_line == r_line

    def test_get_taxon_list1(self, taxon_and_list):
        taxons = get_taxon_list(taxon_and_list["tax_list"].id_liste)
        # autre chose)
        assert taxon_and_list["taxon"].cd_nom in [t[0] for t in taxons]
        assert (
            type(taxons[0][0]) is int and type(taxons[0][1]) is str and type(taxons[0][2]) is str
        )

    def test_get_observer_list1(self, observers_and_list):
        observers = get_observer_list(observers_and_list["list"].id_liste)
        print("observers: ", observers)
        user = observers_and_list["user_list"][0]
        print(observers[0])
        assert user.id_role in [obs[0] for obs in observers]
        assert type(observers) is list
        assert type(observers[0][0]) is int and type(observers[0][1]) is str

    def test_get_site_list1(self, site, module):
        sites = get_site_list(module.id_module)
        print(site, sites)
        assert site.id_base_site in [s[0] for s in sites]
        assert type(sites) is list
        assert type(sites[0][0]) is int and type(sites[0][1]) is str
        geom = sites[0][2].split(" ")
        assert len(geom) == 2

    def test_get_nomenclature_list1(self, nomenclature):
        nomenclatures = get_ref_nomenclature_list(code_nomenclature_type="TEST")
        print(nomenclatures)
        assert nomenclature.id_nomenclature in [nom[1] for nom in nomenclatures]
        assert type(nomenclatures) is list
        assert (
            type(nomenclatures[0][1]) is int
            and type(nomenclatures[0][0]) is str
            and type(nomenclatures[0][2]) is str
            and type(nomenclatures[0][3]) is str
        )

    def test_bidule(self, test):
        user = db.session.query(User).filter_by(identifiant="bidule").one()
        print(user)

    # def test_bidule2(test):
    #     user = db.session.query(UserList).filter_by(identifiant="bidule").one()
    #     print(user)
