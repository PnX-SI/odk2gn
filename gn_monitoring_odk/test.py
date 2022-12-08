from gn_module_monitoring.monitoring.models import TModules

from geonature.utils.env import DB
from geonature import create_app

app = create_app()

with app.app_context():
    data = DB.session.query(TModules).all()

    print(data)
