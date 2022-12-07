import logging
import click

from datetime import datetime
from functools import reduce

from geonature.app import create_app

from gn_module_monitoring.monitoring.models import (
    TMonitoringSites,
    TMonitoringVisits,
    TMonitoringObservations,
)
from geonature.utils.utilsmails import send_mail
from geonature.core.gn_meta.models import TDatasets
from pypnusershub.db.models import User
from sqlalchemy import exc

from geonature.utils.env import DB

from gn_monitoring_odk.config import config
from gn_monitoring_odk.odk_api import get_submissions, get_schema_fields
from gn_monitoring_odk.utils_dict import NestedDictAccessor

# TODO : post visite

import pprint

log = logging.getLogger("app")
log.setLevel(logging.INFO)
pp = pprint.PrettyPrinter(width=41, compact=True)


@click.command()
@click.argument("module_name")
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def synchronize(module_name, project_id, form_id):
    log.info(f"--- Start synchro for module {module_name} ---")
    try:
        schema = config[module_name]
    except KeyError as e:
        log.error(f"No configuration found for module {module_name} ")
        raise
    form_data = NestedDictAccessor(get_submissions(project_id, form_id))
    pp.pprint(form_data[0])
    app = create_app()
    with app.app_context() as app_ctx:
        for sub in form_data:
            sites = DB.session.query(TMonitoringSites).all()

            visite = TMonitoringVisits(
                id_base_site=1,
                id_dataset=9742,
                id_module=1368,
                visit_date_min=datetime.now(),
                visit_date_max=datetime.now(),
                comments="toto",
                data={"debutant": "Oui", "nuages": "0-33%"},
                observers=DB.session.query(User).all(),
            )

            observation = TMonitoringObservations(
                cd_nom=2975, comments="super obs", data={"nb_0_5": 5, "nb_5_10": 2}
            )

            visite.observations.append(observation)

            DB.session.add(visite)

            try:
                DB.session.commit()
                pass
            except exc.SQLAlchemyError as e:
                send_mail(
                    config["gn_odk"]["email_for_error"],
                    subject="Synchronisation ODK error",
                    msg_html=str(e),
                )
                DB.session.rollback()
