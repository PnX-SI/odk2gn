import os
import time

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from flask import current_app
from geonature.utils.celery import celery_app
from odk2gn.commands import synchronize_module, upgrade_module
from odk2gn.config import CentralSchema
from odk2gn.gn2_utils import get_module_code
from odk2gn.models import TOdkForm


logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute="*/1"),
        synchronize_all_modules.s(),
        name="synchronize_monitoring _modules",
    )
    sender.add_periodic_task(
        crontab(minute="*/1"),
        upgrade_all_forms.s(),
        name="upgrade_monitoring_modules",
    )


@celery_app.task(bind=True)
def synchronize_all_modules(self):
    for form in TOdkForm.query.all():
        if form.module.type == "monitoring_module":
            logger.info(f"----Synchronizing module {form.module.module_code}----")
            synchronize_module(
                form.module.module_code,
                project_id=form.odk_project_id,
                form_id=form.odk_form_id,
            )
            logger.info(f"----{form.module.module_code} module synchronized----")
            time.sleep(2)


@celery_app.task(bind=True)
def upgrade_all_forms(self):
    for form in TOdkForm.query.all():
        if form.module.type == "monitoring_module":
            logger.info(f"----Upgrading form for module {form.module.module_code}----")
            upgrade_module(
                form.module.module_code,
                project_id=form.odk_project_id,
                form_id=form.odk_form_id,
                skip_jdd=False,
                skip_nomenclatures=False,
                skip_observers=False,
                skip_sites=False,
                skip_sites_groups=False,
                skip_taxons=False,
            )
            logger.info(f"---{form.module.module_code} module upgraded----")
            time.sleep(2)
