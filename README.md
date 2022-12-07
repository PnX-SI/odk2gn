# ODK collect to

# Installation

```sh
# Création du virtualenv
python3 -m venv venv && source venv/bin/activate && pip install -U pip

# Installation du module
pip install -e .

# Installation de geonature
cd <path_vers_gn>
pip install -e .
cd /backend
pip install -r requirements-dev.in
pip install -r requirements-submodules.in

# Installation du module monitoring
pip install -e <path_vers_gn_module_monitoring>
```

# Commandes

```sh
source venv/bin/activate
```

## Synchronisation des données de odk vers geonature
```sh
synchronize STOM --form_id=Sicen --project_id=1
```