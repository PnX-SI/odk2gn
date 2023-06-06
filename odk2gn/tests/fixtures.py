import pytest

from geonature.utils.env import db
from geonature import create_app
from geonature.core.gn_meta.models import (
    TDatasets,
)

from utils_flask_sqla.tests.utils import JSONClient


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
    return ["Buid a fake list of submissions", "TODO"]


@pytest.fixture(scope="function")
def datasets():
    return [
        TDatasets(id_dataset=1, dataset_name="ds1"),
        TDatasets(id_dataset=2, dataset_name="ds2"),
    ]
