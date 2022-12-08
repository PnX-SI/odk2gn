from pathlib import Path
from toml import load
from gn_monitoring_odk.config_schema import CentralSchema

config = load(Path("config.toml"))

CentralSchema().load(config["central"])
