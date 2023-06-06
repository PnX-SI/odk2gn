from pathlib import Path
from toml import load
from odk2gn.gn2_utils import find_all, find_odk_path
from odk2gn.config_schema import CentralSchema
import os




        
paths = find_all("config.toml","/")
odk_path = find_odk_path(paths=paths)


config = load(Path(odk_path))

CentralSchema().load(config["central"])
