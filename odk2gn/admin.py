from flask_admin.babel import gettext
from flask_admin.contrib.sqla import ModelView
from geonature.core.admin.admin import CruvedProtectedMixin
from geonature.core.admin.admin import admin as flask_admin
from geonature.utils.env import DB


from odk2gn.models import TOdkForm


class OdkFormModelView(CruvedProtectedMixin, ModelView):
    module_code = "ODK2GN"
    object_code = "ODK2GN_SYNCHRO"


flask_admin.add_view(
    OdkFormModelView(model=TOdkForm, session=DB.session, name="Synchronisation ODK", category="odk2gn")
)
