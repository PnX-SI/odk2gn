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
    id_base_site = fields.Str()
    id_dataset = fields.Str()
    # default_id_dataset = fields.Str()
    date_min = fields.Str()
    date_max = fields.Str()
    data = fields.List(fields.Str())
    observers_repeat = fields.Str(load_default="observer")
    id_observer = fields.Str(load_default="id_role")
    media = fields.Str(load_default="medias_visit")
    media_type = fields.Str(
        load_default="Photo",
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"]),
    )
    comments = fields.Str(load_default="comments_visit")


class ObservationSchema(Schema):
    path = fields.Str(load_default="observation")
    comments = fields.Str()
    media = fields.Str(load_default="medias_observation")
    media_type = fields.Str(
        load_default="Photo",
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"]),
    )
    comments = fields.Str(load_default="comments_observation")


class ProcoleSchema(Schema):
    SITE = fields.Nested(SiteSchema)
    VISIT = fields.Nested(VisitSchema)
    OBSERVATION = fields.Nested(ObservationSchema)
