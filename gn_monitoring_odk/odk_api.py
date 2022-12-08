import logging

from pyodk.client import Client

log = logging.getLogger("app")

client = Client(config_path="./config.toml")


def get_attachment(project_id, form_id, uuid_sub, media_name):
    print(
        "URL BIS##################",
        f"projects/{project_id}/forms/{form_id}/submissions/{uuid_sub}/attachments/{media_name}",
    )
    img = client.get(
        f"projects/{project_id}/forms/{form_id}/submissions/{uuid_sub}/attachments/{media_name}"
    )
    return img


def get_submissions(project_id, form_id):
    # Creation client odk central
    form_data = None
    with client:
        form_data = client.submissions.get_table(
            form_id=form_id,
            project_id=project_id,
            expand="*",
            # filter="__system/submissionDate ge 2022-12-06T14:56:00.000Z"
            # filter= "__system/reviewState not rejected"
        )
        return form_data["value"]


def get_attachments(project_id, form_data):
    # #########################################
    #  Attachments
    # projects/1/forms/Sicen/submissions/{data['__id']}/attachments => Récupération de la liste des attachments pour une soumissions
    # projects/1/forms/Sicen/submissions/{data['__id']}/attachments/{att['name']} => Téléchargement de l'attachment pour la soumission
    for data in form_data:
        attachments_list = client.get(
            f"projects/1/forms/Sicen/submissions/{data['__id']}/attachments"
        )
        print("Nombre de médias", {data["__id"]}, len(attachments_list.json()))
        print(attachments_list.json())
        for att in attachments_list.json():
            img = client.get(
                f"projects/{project_id}/forms/Sicen/submissions/{data['__id']}/attachments/{att['name']}"
            )
            print(
                "URL###################",
                f"projects/{project_id}/forms/Sicen/submissions/{data['__id']}/attachments/{att['name']}",
            )
            with open(att["name"], "wb") as out_file:
                out_file.write(img.content)


def get_schema_fields(project_id, xml_form_id):
    resp = client.get(f"projects/{project_id}/forms/{xml_form_id}/fields?odata=false")
    return resp.json()


class ODKSchema:
    def __init__(self, project_id, form_id):
        self.project_id = project_id
        self.form_id = form_id
        self.schema = self._get_schema_fields()

    def _get_schema_fields(self):
        with client:
            resp = client.get(
                f"projects/{self.project_id}/forms/{self.form_id}/fields?odata=false"
            )
            assert resp.status_code == 200
            return resp.json()

    def get_field_info(self, field_name):
        try:
            return next(field for field in self.schema if field["name"] == field_name)
        except StopIteration:
            log.error(f"the field {field_name} does not exist in this ODK form")
            raise
