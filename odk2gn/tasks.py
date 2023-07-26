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
from odk2gn.gn2_utils import get_module_code
from odk2gn.models import TOdkForm


logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour="*/1"),
        synchronize_all_modules.s(),
        name="synchronize_all",
    )
    sender.add_periodic_task(
        crontab(minute="0", hour="12"),
        upgrade_all_forms.s(),
        name="upgrade_all",
    )


def get_odk_modules():
    modules = (TModules).query.filter(TModules.id_module == TOdkForm.id_module).all()
    return modules


def get_odk_data(module):
    form_id = (TOdkForm.odk_form_id).filter_by(id_module=module.id_module)
    project_id = (TOdkForm.odk_project_id).filter_by(id_module=module.id_module)
    return {"project_id": project_id, "form_id": form_id}


@celery_app.task(bind=True)
def synchronize_all_modules(self):
    modules = get_odk_modules()
    for module in modules:
        logger.info(f"----Synchronizing module {module.module_code}----")
        synchronize_monitoring(
            module.module_code,
            project_id=get_odk_data(module)["project_id"],
            form_id=get_odk_data(module)["form_id"],
        )
        logger.info(f"----{module.module_code} module synchronized----")


@celery_app.task(bind=True)
def upgrade_all_forms(self):
    modules = get_odk_modules()
    for module in modules:
        logger.info(f"----Upgrading form for module {module.module_code}----")
        upgrade_monitoring(
            module.module_code,
            project_id=get_odk_data(module)["project_id"],
            form_id=get_odk_data(module)["form_id"],
        )
        logger.info(f"---{module.module_code} module upgraded----")
