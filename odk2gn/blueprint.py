import logging

from flask import Blueprint

# TODO : celery
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
