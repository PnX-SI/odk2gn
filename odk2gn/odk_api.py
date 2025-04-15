import logging
import requests
import json

from datetime import datetime
from pyodk.client import Client

from geonature.utils.module import get_module_config_path


odk2gn_config_file = get_module_config_path("ODK2GN")
log = logging.getLogger("app")

client = Client(config_path=odk2gn_config_file)


def get_attachment(project_id, form_id, uuid_sub, media_name):
    print("URL", f"projects/{project_id}/forms/{form_id}/submissions/{uuid_sub}/attachments/{media_name}")
    img = client.get(
        f"projects/{project_id}/forms/{form_id}/submissions/{uuid_sub}/attachments/{media_name}"
    )
    if img.status_code == 200:
        return img.content
    else:
        log.warning(f"No image found for submission {uuid_sub}")



def get_submissions(project_id, form_id):
    # Creation client odk central
    form_data = None
    with client:
        form_data = client.submissions.get_table(
            form_id=form_id,
            project_id=project_id,
            expand="*",
            # TODO : try received or edited (but edited not actually support)
            # filter="__system/reviewState ne 'approved' and __system/reviewState ne 'hasIssues' and __system/reviewState ne 'rejected'",
            # filter="__system/reviewState eq 'rejected'",
        )
        return form_data["value"]



def update_review_state(project_id, form_id, submission_id, review_state):
    """Update the review state

    :param projet id : the project id
    :type projecet_id: int

    :param form_id id : the xml form id
    :type form_id: str

    :param review_state id : the value of the state for update
    :type form_id: str ("approved", "hasIssues", "rejected")
    """
    token = client.session.auth.service.get_token(
        username=client.config.central.username,
        password=client.config.central.password,
    )
    # pourquoi classe requests ici et non la methode de la classe Client de pyODK?
    review_submission_response = client.patch(
        f"{client.config.central.base_url}/v1/projects/{project_id}/forms/{form_id}/submissions/{submission_id}",
        data=json.dumps({"reviewState": review_state}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
    )
    try:
        assert review_submission_response.status_code == 200
    except AssertionError:
        log.error("Error while update submision state")


def update_form_attachment(project_id, xml_form_id, files):
    """Mise à jour du formulaires
        3 étapes :
         1 - passer le formulaire en draft
         2 - mettre à jour les médias
         3 - publier le formulaires
    :param project_id: id du projet
    :type project_id: int
    :param xml_form_id: nom du formulaire
    :type xml_form_id: str
    :param files: dictionnaires des fichiers à poster
    :type files: dict
    """
    form_draft(project_id, xml_form_id)
    for file_name in files:
        upload_form_attachment(project_id, xml_form_id, file_name=file_name, data=files[file_name])
    publish_form(project_id, xml_form_id)


def form_draft(project_id, xml_form_id):
    """Publie une ébauche du formulaire

    TODO : mette à jour la définition du formulaire

    :param project_id: id du projet
    :type project_id: int
    :param xml_form_id: nom du formulaire
    :type xml_form_id: str
    """
    with client:
        request = client.post(f"projects/{project_id}/forms/{xml_form_id}/draft")
        assert request.status_code == 200


def upload_form_attachment(project_id, xml_form_id, file_name, data):
    """Upload fichier attaché du formulaire

    :param project_id: id du projet
    :type project_id: int
    :param xml_form_id: nom du formulaire
    :type xml_form_id: str
    :param file_name: nom du fichier
    :type file_name: str
    :param data: csv data converti en chaine de caractères
    :type data: str
    """
    response = client.post(
        f"{client.config.central.base_url}/v1/projects/{project_id}/forms/{xml_form_id}/draft/attachments/{file_name}",
        data=data.encode("utf-8", "strict"),
    )
    if response.status_code == 404:
        log.warning(f"Le fichier {file_name} n'existe pas dans la définition du formulaire")
    elif response.status_code == 200:
        log.info(f"fichier {file_name} téléversé")
    else:
        # TODO raise error
        pass


def publish_form(project_id, xml_form_id):
    """Publication du formulaire avec un nouveau numéro de version
        :param project_id: id du projet
    :type project_id: int
    :param xml_form_id: nom du formulaire
    :type xml_form_id: str
    """
    version_number = datetime.now()
    response = client.post(
        f"projects/{project_id}/forms/{xml_form_id}/draft/publish?version={version_number}"
    )
    assert response.status_code == 200


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
