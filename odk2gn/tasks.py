import os

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from geonature.core.gn_commons.models import TModules
from flask import current_app
from geonature.utils.celery import celery_app
from odk2gn.commands import synchronize_monitoring, upgrade_monitoring
from odk2gn.config import CentralSchema


logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute="*/1"),
        synchronize_all_modules.s(form_ids=form_ids),
        name="synchronize_all",
    )
    sender.add_periodic_task(
        crontab(minute="0", hour="12"),
        upgrade_all_forms.s(form_ids=form_ids),
        name="upgrade_all",
    )


def get_monitoring_modules():
    modules = (TModules).query.filter_by(type="monitoring_module").all()
    return modules


form_ids = {"STOM": "stom_form", "chiro": "form_odk_chiro", "suivi_nardaie": "nard_test"}


@celery_app.task(bind=True)
def synchronize_all_modules(self, form_ids):
    modules = get_monitoring_modules()
    for module in modules:
        logger.info(f"----Synchronizing module {module.module_code}----")
        synchronize_monitoring(
            module.module_code,
            project_id=6,
            form_id=form_ids[module.module_code],
        )
        logger.info(f"----{module.module_code} module synchronized----")


@celery_app.task(bind=True)
def upgrade_all_forms(self, form_ids):
    modules = get_monitoring_modules()
    for module in modules:
        logger.info(f"----Upgrading form for module {module.module_code}----")
        upgrade_monitoring(
            module.module_code,
            project_id=6,
            form_id=form_ids[module.module_code],
        )
        logger.info(f"---{module.module_code} module upgraded----")
