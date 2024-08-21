from sqlalchemy import select, func, and_
from sqlalchemy.orm import column_property
from sqlalchemy.dialects.postgresql import JSONB, UUID
from uuid import uuid4

from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable

from sqlalchemy.ext.hybrid import hybrid_property


from geonature.core.gn_commons.models import TMedias
from geonature.core.gn_monitoring.models import TBaseSites, TBaseVisits
from geonature.core.gn_meta.models import TDatasets
from geonature.utils.env import DB
from geonature.core.gn_commons.models import TModules, cor_module_dataset
from pypnusershub.db.models import User


class TOdkForm(DB.Model):
    __tablename__ = "t_odk_forms"
    __table_args__ = {"schema": "odk2gn"}

    id = DB.Column(DB.Integer, primary_key=True, nullable=False, unique=True)
    odk_form_id = DB.Column(DB.String, unique=True, nullable=False)
    id_module = DB.Column(
        DB.ForeignKey("gn_commons.t_modules.id_module"),
        nullable=False,
    )
    odk_project_id = DB.Column(DB.Integer, nullable=False)
    synchronize_command_name = DB.Column(DB.String, nullable=False)
    upgrade_command_name = DB.Column(DB.String, nullable=False)

    module = DB.relationship(TModules, lazy="joined")
