import pytest

from odk2gn.tests.fixtures import app, submissions, _session, datasets, header, data, taxon, module, point
from odk2gn.tests.fixtures import site
from odk2gn.gn2_utils import get_jdd_list, to_csv, get_site_list, get_taxon_list
from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import to_wkt
#from odk2gn.odk_api import dummy



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


@pytest.mark.usefixtures()
class TestUtilsFunctions:
    def test_get_jdd_list1(self, datasets):
        formated_ds = get_jdd_list(datasets)
        assert formated_ds == [[1, "ds1"], [2, "ds2"]]
    
    def test_to_csv1(self, header, data):
        csv = to_csv(header, data) 
        assert csv == "column1,column2"+'\n'+'1,2'+'\n'+'3,4'
    
    def test_get_taxon_list1(self, taxon):
        taxons = get_taxon_list(100)
        assert taxon in taxons

    def test_get_site_list1(self, site, module):
        sites = get_site_list(module.id_module)
        assert site in sites
    
    #def test_get_nomenclature_list1(self, module):

    
    

