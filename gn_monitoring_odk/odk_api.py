from pyodk.client import Client

client = Client(config_path="./config.toml")


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
        # print("Nombre de données de la requête", len(form_data["value"]))
        # print(form_data)
        return form_data["value"]


def get_attachments(project_id, form_data):
    # #########################################
    #  Attachments
    # projects/1/forms/Sicen/submissions/{data['__id']}/attachments => Récupération de la liste des attachments pour une soumissions
    # projects/1/forms/Sicen/submissions/{data['__id']}/attachments/{att['name']} => Téléchargement de l'attachment pour la soumission
    for data in form_data["value"]:
        attachments_list = client.get(
            f"projects/1/forms/Sicen/submissions/{data['__id']}/attachments"
        )
        print("Nombre de médias", {data["__id"]}, len(attachments_list.json()))
        print(attachments_list.json())
        for att in attachments_list.json():
            img = client.get(
                f"projects/{project_id}/forms/Sicen/submissions/{data['__id']}/attachments/{att['name']}"
            )
            with open(att["name"], "wb") as out_file:
                out_file.write(img.content)


def get_schema_fields(project_id, xml_form_id):
    resp = client.get(f"projects/{project_id}/forms/{xml_form_id}/fields?odata=false")
    return resp.json()
