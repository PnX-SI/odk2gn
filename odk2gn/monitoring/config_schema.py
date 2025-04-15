from marshmallow import Schema, fields
from marshmallow.validate import OneOf


class SiteSchema(Schema):
    create_site = fields.Str(load_default="create_site")
    base_site_name = fields.Str(load_default="site_name")
    base_site_description = fields.Str(load_default="base_site_description")
    first_use_date = fields.Str(load_default="visit_date_min")
    id_inventor = fields.Str(load_default="observers")
    geom = fields.Str(load_default="geom")
    site_group = fields.Str(load_default="site_group")


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
    module_code = fields.Str(required=True)
    can_create_site = fields.Boolean(load_default=True)
    SITE = fields.Nested(SiteSchema, load_default=SiteSchema().load({}))
    VISIT = fields.Nested(VisitSchema, load_default=VisitSchema().load({}))
    OBSERVATION = fields.Nested(ObservationSchema, load_default=ObservationSchema().load({}))
