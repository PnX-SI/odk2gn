import os
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from flask import current_app
from geonature.utils.celery import celery_app
from odk2gn.commands import synchronize_module, upgrade_module
from odk2gn.gn2_utils import get_module_code
from odk2gn.models import TOdkForm

from geonature.utils.config import config

cron = config["ODK2GN"]["tasks"]


if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sync_cron = cron["synchronize_schedule"].split(" ")
    sender.add_periodic_task(
        crontab(
            minute=sync_cron[0],
            hour=sync_cron[1],
            day_of_week=sync_cron[2],
            day_of_month=sync_cron[3],
            month_of_year=sync_cron[4],
        ),
        synchronize_all_modules.s(),
        name="synchronize_monitoring_modules",
    )
    upgrade_cron = cron["upgrade_schedule"].split(" ")
    sender.add_periodic_task(
        crontab(
            minute=upgrade_cron[0],
            hour=upgrade_cron[1],
            day_of_week=upgrade_cron[2],
            day_of_month=upgrade_cron[3],
            month_of_year=upgrade_cron[4],
        ),
        upgrade_all_forms.s(),
        name="upgrade_monitoring_modules",
    )


from click import Context
from odk2gn.commands import synchronize_monitoring, synchronize, upgrade_odk_form


@celery_app.task(bind=True)
def synchronize_all_modules(self):
    for form in TOdkForm.query.all():
        logger.info(f"----Synchronizing module {form.module.module_code}----")
        for key, cmd in synchronize.commands.items():
            if form.upgrade_command_name == cmd.name:
                if form.module.type == "monitoring_module":
                    cmd.callback(
                        module_code=form.module.module_code,
                        project_id=form.odk_project_id,
                        form_id=form.odk_form_id,
                    )
                else:
                    cmd.callback(project_id=form.odk_project_id, form_id=form.odk_form_id)
        logger.info(f"----{form.module.module_code} module synchronized at----")
        time.sleep(2)


@celery_app.task(bind=True)
def upgrade_all_forms(self):
    for form in TOdkForm.query.all():
        logger.info(f"----Upgrading form for module {form.module.module_code}----")
        for key, cmd in upgrade_odk_form.commands.items():
            if form.upgrade_command_name == cmd.name:
                if form.module.type == "monitoring_module":
                    cmd.callback(
                        module_code=form.module.module_code,
                        project_id=form.odk_project_id,
                        form_id=form.odk_form_id,
                        skip_taxons=False,
                        skip_sites=False,
                        skip_jdd=False,
                        skip_sites_groups=False,
                        skip_nomenclatures=False,
                        skip_observers=False,
                    )
                else:
                    cmd.callback(project_id=form.odk_project_id, form_id=form.odk_form_id)
        logger.info(f"---{form.module.module_code} module upgraded----")
        time.sleep(2)
