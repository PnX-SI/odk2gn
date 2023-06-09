import pytest
import uuid

from odk2gn.contrib.flore_proritaire.src.odk_flore_prioritaire.odk_methods import to_wkt
from geonature.utils.env import db
from geonature import create_app
from geonature.core.gn_meta.models import (
    TDatasets
)
from sqlalchemy.event import listen, remove
from geonature.core.gn_commons.models import TModules

from pypnusershub.db.models import UserList, User
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from geonature.core.gn_monitoring.models import TBaseSites, corSiteModule
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules, TMonitoringSites
)
from apptax.taxonomie.models import BibListes, CorNomListe, Taxref, BibNoms
from utils_flask_sqla.tests.utils import JSONClient

point = {
    "geometry": {
    "type": "Point",
    "coordinates": [6.0535113, 44.5754145]
  }
}

def get_site_type():
    site_type = (BibNomenclaturesTypes.query.filter_by(mnemonique='TYPE_SITE').first())
    return site_type

@pytest.fixture(scope='function')
def taxon():
    taxon = (815096, 'Homo sapiens Linnaeus, 1758','Homme moderne, Homme de Cro-Magnon')
    return taxon


@pytest.fixture(scope="session", autouse=True)
def app():
    app = create_app()
    app.testing = True
    app.test_client_class = JSONClient
    app.config["SERVER_NAME"] = "test.geonature.fr"  # required by url_for

    with app.app_context():
        """
        Note: This may seem redundant with 'temporary_transaction' fixture.
        It is not as 'temporary_transaction' has a function scope.
        This nested transaction is useful to rollback class-scoped fixtures.
        Note: As we does not have a complex savepoint restart mechanism here,
        fixtures must commit their database changes in a nested transaction
        (i.e. in a with db.session.begin_nested() block).
        """
        transaction = db.session.begin_nested()  # execute tests in a savepoint
        yield app
        transaction.rollback()  # rollback all database changes


@pytest.fixture
def _session(app):
    return db.session




@pytest.fixture()
def submissions():
    return [{'sub_id': 1, 'taxon': 'Homo sapiens'}, {'sub_id' : 22, 'taxon' : 'Nardus stricta'}]


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
        db.session.commit()
    return new_module

@pytest.fixture(scope='function')
def header():
    return "column1", "column2"

@pytest.fixture(scope='function')
def data():
    return ('1' +'2'), ('3','4')

@pytest.fixture(scope='function')
def nomenclature():
    with db.session.begin_nested():

        type_nom = BibNomenclaturesTypes(
        mneumonique = 'TEST',
        label_default = 'test', 
        label_fr = 'Test'
        )
        db.session.flush()
        nomenclature = TNomenclatures(
            id_type = type_nom.id_nomenclature,
            cd_nomenclature = 'test',
            label_default = 'test', 
            label_fr = 'Test',
            active = True
        )
        db.session.add(type_nom, nomenclature)      
        db.session.commit()  
    return nomenclature

@pytest.fixture(scope='function')
def site():
    
    with db.session.begin_nested():
        id_site_type = (BibNomenclaturesTypes.id_type).query.filter(BibNomenclaturesTypes.mnemonique=='TYPE_SITE').first()
        nom = TNomenclatures(
            id_type = id_site_type,
            cd_nomenclature = 'test_site',
            label_default = 'test_site', 
            label_fr = 'Site Test',
            active = True
        )
        db.session.add(nom)
        db.session.flush()

        test_site=TBaseSites(
        base_site_name = "test_site", 
        geom = to_wkt(point['geometry']),
        id_nomenclature_type_site = nom.id_nomenclature
        )
        db.session.add(test_site)        
    return test_site


