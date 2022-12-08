from gn_module_monitoring.config.repositories import get_config



def get_nomenclatures_fields(module_code: str, niveau: str):
    config = get_config(module_code)
    if not config:
        return []
    if not niveau in config:
        return []

    fields = dict(
        config[niveau].get("specific", []),
        **config[niveau].get("generic", []),
    )
    nomenclatures_fields = []
    for name in fields:
        form = fields[name]
        type_util = form.get('type_util')
        type_widget = form.get('type_widget')

        # composant nomenclature
        if type_widget == 'nomenclature':
            nomenclatures_fields.append({
                "code_nomenclature_type": form["code_nomenclature_type"],
                "cd_nomenclatures": form.get("cd_nomenclatures", None)
            })

        # composant datalist
        if type_widget == 'datalist':
            if type_util == "nomenclature":
                code_nomenclature_type = form.get('api').split('/')[-1]
                nomenclatures_fields.append({
                    "code_nomenclature_type": code_nomenclature_type,
                    "regne": form.get("params", {}).get("regne"),
                    "group2_inpn": form.get("params", {}).get("group2_inpn"),
                })
    return nomenclatures_fields

