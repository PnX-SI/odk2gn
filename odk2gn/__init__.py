import sys
import logging
import colorlog

from importlib.metadata import entry_points

from odk2gn.main import synchronize, upgrade_odk_form

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(levelname)s:%(name)s:%(message)s"))

root_logger = logging.getLogger("app")
root_logger.addHandler(handler)
root_logger.propagate = False


for contrib in entry_points(group="gn_odk_contrib", name="synchronize"):
    synchronize_cmd = contrib.load()
    synchronize.add_command(synchronize_cmd)

for contrib in entry_points(group="gn_odk_contrib", name="upgrade_odk_form"):
    upgrade_form_cmd = contrib.load()
    upgrade_odk_form.add_command(upgrade_form_cmd)
