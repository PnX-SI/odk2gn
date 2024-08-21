from flask_admin.babel import gettext
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import is_form_submitted
from flask_wtf import Form
from geonature.core.admin.admin import CruvedProtectedMixin
from geonature.core.admin.admin import admin as flask_admin
from geonature.core.gn_commons.models import TModules
from geonature.core.users.models import CorRole
from geonature.utils.env import DB
from psycopg2.errors import ForeignKeyViolation
from pypnusershub.db.models import (
    Application,
    AppRole,
    User,
    UserApplicationRight,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from utils_flask_sqla_geo.generic import GenericQueryGeo
from wtforms import validators, StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired

from odk2gn.models import TOdkForm
from odk2gn.gn2_utils import get_monitoring_modules


class OdkFormModelView(CruvedProtectedMixin, ModelView):
    module_code = "ODK2GN"
    object_code = "ODK2GN_SYNCHRO"


flask_admin.add_view(
    OdkFormModelView(model=TOdkForm, session=DB.session, name="Synchronisation ODK", category="odk2gn")
)
