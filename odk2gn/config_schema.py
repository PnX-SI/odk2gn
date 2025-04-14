from marshmallow import Schema, fields


class Odk2GnTaskSchema(Schema):
    synchronize_schedule = fields.Str(load_default="0 0 * * *")
    upgrade_schedule = fields.Str(load_default="0 0 * * *")


class CentralSchema(Schema):
    base_url = fields.URL(required=True)
    username = fields.String(required=True)
    password = fields.String(required=True)
    default_project_id = fields.Int()


class GnODK(Schema):
    email_for_error = fields.Email()


class Odk2GnSchema(Schema):
    central = fields.Nested(CentralSchema)
    tasks = fields.Nested(Odk2GnTaskSchema)
    email_for_error = fields.Nested(GnODK)
    # On ne peut pas ajouter ProcoleSchema ici, il est lié à monitoring
    modules = fields.List(fields.Dict)
