from pathlib import Path
from marshmallow import Schema
from toml import load
from odk2gn.config_schema import CentralSchema


class EmptySchema(Schema):
    pass


config_file = Path(__file__).absolute().parent.parent / "config.toml"

config = load(Path(config_file))

CentralSchema().load(config["central"])
