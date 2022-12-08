from marshmallow import Schema, fields, validate
from marshmallow.validate import OneOf


class CentralSchema(Schema):
    base_url = fields.URL(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    default_project_id = fields.Int()


class GnODK(Schema):
    email_for_error = fields.Email()


class SiteSchema(Schema):
    media_name = fields.Str()
    media_type = fields.Str(
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"])
    )


class VisitSchema(Schema):
    id_base_site = fields.Str(required=True)
    id_dataset = fields.Str()
    default_id_dataset = fields.Str()
    date_min = fields.Str(required=True)
    date_max = fields.Str()
    data = fields.List(fields.Str(), required=True)
    observers = fields.Str(required=True)
    observations = fields.Str(required=True)
    media_name = fields.Str()
    media_type = fields.Str(
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"])
    )


class ObservationSchema(Schema):
    cd_nom = fields.Str(required=True)
    comments = fields.Str()
    data = fields.List(fields.Str(), required=True)
    media_name = fields.Str()
    media_type = fields.Str(
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"])
    )


class ProcoleSchema(Schema):
    SITE = fields.Nested(SiteSchema)
    VISIT = fields.Nested(SiteSchema)
    OBSERVATION = fields.Nested(SiteSchema)
