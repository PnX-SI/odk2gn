import logging
import pprint
import sys

import click



if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


from geonature.utils.config import config
from odk2gn.odk_api import (
    ODKSchema,
)
from odk2gn.tasks import *

# TODO : post visite


log = logging.getLogger("app")
log.setLevel(logging.INFO)
pp = pprint.PrettyPrinter(width=41, compact=True)


# Commandes
@click.group(name="synchronize")
def synchronize():
    pass


@click.group(name="upgrade-odk-form")
def upgrade_odk_form():
    pass


for contrib in entry_points(group="gn_odk_contrib", name="synchronize"):
    synchronize_cmd = contrib.load()
    synchronize.add_command(synchronize_cmd)

for contrib in entry_points(group="gn_odk_contrib", name="upgrade_odk_form"):
    upgrade_form_cmd = contrib.load()
    upgrade_odk_form.add_command(upgrade_form_cmd)


@click.command()
@click.option("--project_id", required=True, type=int)
@click.option("--form_id", required=True, type=str)
def get_schema(project_id, form_id):
    odk_schema = ODKSchema(project_id, form_id)
    pp.pprint(odk_schema.schema)


module_monitoring_installed = False
try:
    from gn_module_monitoring.monitoring.models import TMonitoringSites
    module_monitoring_installed = True
except ImportError:
    pass

if module_monitoring_installed:
    from odk2gn.monitoring.command import synchronize_module, upgrade_module