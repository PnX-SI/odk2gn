from flask import Markup, current_app, flash
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

from odk2gn.models import TOdkForm
from odk2gn.gn2_utils import get_monitoring_modules


class OdkFormModelView(ModelView):
    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(OdkFormModelView, self).__init__(TOdkForm, session, **kwargs)

    can_create = True
    can_edit = False
    can_delete = True

    column_list = (TOdkForm.odk_form_id, TOdkForm.odk_project_id, "module_code")

    class ODKForm(Form):
        odk_form_id_field = StringField()
        odk_project_id_field = StringField()
        module_field = SelectField(choices=get_monitoring_modules())
        submit = SubmitField()

    def get_list():
        list = []
        count = 0
        forms = TOdkForm.query.all()
        for form in forms:
            count += 1
            list.append(form)
        return (count, list)

    def get_one(id):
        form = TOdkForm.query.filter_by(id=id)
        return form

    def create_model(self, form: ODKForm):
        if form.validate_on_submit():
            odk_form = TOdkForm(
                odk_form_id=form.odk_form_id_field.data,
                odk_project_id=form.odk_project_id_field.data,
                id_module=(TModules.id_module).query.filter_by(module_code=form.module_field.data),
            )
            DB.session.add(odk_form)
            DB.session.commit()

    def delete_model(self, form):
        pass


flask_admin.add_view(OdkFormModelView(DB.session, name="Formulaires ODK", category="odk2gn"))
