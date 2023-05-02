from marshmallow import Schema, fields, validate
from marshmallow.validate import OneOf


class CentralSchema(Schema):
    base_url = fields.URL(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    default_project_id = fields.Int()


class GnODK(Schema):
    email_for_error = fields.Email()


class VisitSchema(Schema):
    
    observers_repeat = fields.Str(load_default="observers")
    id_observer = fields.Str(load_default="id_role")
    media = fields.Str(load_default="medias_visit")
    media_type = fields.Str(
        load_default="Photo",
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"]),
    )
    comments = fields.Str(load_default="comments_visit")


class ObservationSchema(Schema):
    observations_repeat = fields.Str(load_default="observations")
    comments = fields.Str()
    media = fields.Str(load_default="medias_observation")
    media_type = fields.Str(
        load_default="Photo",
        validate=OneOf(["Photo", "PDF", "Audio", "Vidéo (fichier)"]),
    )
    comments = fields.Str(load_default="comments_observation")


class ProcoleSchema(Schema):
    VISIT = fields.Nested(VisitSchema, load_default=VisitSchema().load({}))
    OBSERVATION = fields.Nested(
        ObservationSchema, load_default=ObservationSchema().load({})
    )
