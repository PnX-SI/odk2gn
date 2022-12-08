# ODK Central to GeoNature

Module python utilisant les modèles de GeoNature pour intégrer des données depuis l'API d'ODK Central vers la base de données de GeoNature, en utilisant pyodk.

Il permet actuellement d'importer des données collectées avec ODK vers le module Monitoring de GeoNature.

## Installation

```sh
# Création du virtualenv
python3 -m venv venv && source venv/bin/activate && pip install -U pip

# Installation du module
pip install -e .

# Installation de GeoNature
cd <path_vers_gn>
pip install -e .
cd /backend
pip install -r requirements-dev.in
pip install -r requirements-submodules.in

# Installation du module Monitoring
pip install -e <path_vers_gn_module_monitoring>
```

## Commandes

```sh
source venv/bin/activate
```

## Synchronisation des données de ODK vers GeoNature

```sh
synchronize STOM --form_id=form_workshop --project_id=4
```
