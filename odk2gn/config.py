from pathlib import Path
from toml import load
from odk2gn.config_schema import CentralSchema
import os




        

config_file = Path(__file__).absolute().parent.parent / "config.toml"

config = load(Path(config_file))

CentralSchema().load(config["central"])
