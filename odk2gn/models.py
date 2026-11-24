from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from geonature.utils.env import DB
from geonature.core.gn_commons.models import TModules


class TOdkForm(DB.Model):
    __tablename__ = "t_odk_forms"
    __table_args__ = {"schema": "odk2gn"}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False, unique=True
    )
    odk_form_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    id_module: Mapped[int] = mapped_column(
        ForeignKey("gn_commons.t_modules.id_module"),
        nullable=False,
    )
    odk_project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    synchronize_command_name: Mapped[str] = mapped_column(String, nullable=False)
    upgrade_command_name: Mapped[str] = mapped_column(String, nullable=False)

    module: Mapped[TModules] = DB.relationship(TModules, lazy="joined")
