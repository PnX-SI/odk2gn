from pathlib import Path
from toml import load
from odk2gn.config_schema import CentralSchema

config = load(Path("config.toml"))

CentralSchema().load(config["central"])
