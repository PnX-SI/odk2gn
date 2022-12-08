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
    observers_repeat = fields.Str(load_default="observers")
    id_observer = fields.Str(load_default="id_role")
    media = fields.Str(load_default="visit_medias")
    media_type = fields.Str(
        load_default="Photo",
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"]),
    )
    comments = fields.Str(load_default="visit_comments")


class ObservationSchema(Schema):
    path = fields.Str(load_default="observations/especes")
    cd_nom = fields.Str(required=True)
    comments = fields.Str()
    data = fields.List(fields.Str(), required=True)
    media = fields.Str(load_default="observation_media")
    media_type = fields.Str(
        load_default="Photo",
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"]),
    )
    comments = fields.Str(load_default="observation_comments")


class ProcoleSchema(Schema):
    SITE = fields.Nested(SiteSchema)
    VISIT = fields.Nested(VisitSchema)
    OBSERVATION = fields.Nested(ObservationSchema)
