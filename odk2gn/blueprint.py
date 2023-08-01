import sys
import click

from flask import Blueprint


import logging
import click
import uuid


import flatdict

from sqlalchemy.orm import exc
from sqlalchemy.exc import SQLAlchemyError
from geonature.utils.env import BACKEND_DIR
from gn_module_monitoring.config.repositories import get_config
from geonature.utils.utilsmails import send_mail
from pypnusershub.db.models import User
from geonature.core.gn_commons.models import BibTablesLocation
from pypnnomenclature.models import TNomenclatures
from gn_module_monitoring.monitoring.models import TMonitoringSites
from geonature.core.gn_monitoring.models import TBaseSites
from geonature.core.gn_commons.models import TMedias
from geonature.utils.env import DB
from odk2gn.odk_api import (
    get_submissions,
    update_form_attachment,
    ODKSchema,
    update_review_state,
    get_attachment,
)
from odk2gn.monitoring_utils import (
    parse_and_create_visit,
    parse_and_create_obs,
    parse_and_create_site,
)
from odk2gn.config_schema import ProcoleSchema

from odk2gn.gn2_utils import get_modules_info, get_gn2_attachments_data, write_real_csvs

###### TODO : celery
from .tasks import *
from .admin import *

####### Commandes
from odk2gn.commands import synchronize, upgrade_odk_form

# TODO : post visite

import pprint

log = logging.getLogger("app")
log.setLevel(logging.INFO)
pp = pprint.PrettyPrinter(width=41, compact=True)


blueprint = Blueprint("odk2gn", __name__)

blueprint.cli.add_command(synchronize)
blueprint.cli.add_command(upgrade_odk_form)

print(config["ODK2GN"])
