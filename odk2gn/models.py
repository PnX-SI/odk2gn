from geonature.utils.env import DB
from geonature.core.gn_commons.models import TModules

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
