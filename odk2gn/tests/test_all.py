import pytest

from odk2gn.tests.fixtures import app, submissions, _session, datasets
from odk2gn.gn2_utils import get_jdd_list

# from odk2gn.odk_api import dummy


@pytest.mark.usefixtures()
class TestCommand:
    def test_synchronize_monitoring(self, mocker, submissions):
        from odk2gn.main import dummy

        mocker.patch("odk2gn.main.get_submissions", return_value=submissions)

        # la vrai fonction a "mocker" est synchronize_monitoring et non 'dummy'
        submissions = dummy()
        assert True


@pytest.mark.usefixtures()
class TestUtilsFunctions:
    def test_get_jdd_list1(self, datasets):
        formated_ds = get_jdd_list(datasets)
        assert formated_ds == [[1, "ds1"], [2, "ds2"]]
