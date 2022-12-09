# ODK Central to GeoNature

ODK2GN est un module python utilisant les modèles de GeoNature pour intégrer des données depuis l'API d'ODK Central vers la base de données de GeoNature, en utilisant pyodk.

Il permet actuellement d'importer des données collectées avec ODK vers le module Monitoring de GeoNature et de mettre à jour les listes de valeurs du formulaire ODK en fonction des données de la base de données GeoNature, en se basant sur les fichiers de configuration du module Monitoring.

## Architecture

![Architecture](docs/img/archi_global.jpeg)

## Installation

Bien qu'indépendant, l'installation de ce module se fait dans l'environnement de GeoNature.

```sh
# Activation du virtual env de GeoNature
source <path_vers_gn>/backend/venv/bin/activate

# Installation du module
pip install -e .
```

## Configuration

**ODK central**

Renseigner les paramètres de connexion au serveur ODK Central, pour `pyODK` (https://github.com/getodk/pyodk)

```
[central]
base_url = "https://odk-central.monserveur.org"
username = "username"
password = "password"
default_project_id = 1
```

**Modules monitoring**

Les formulaire monitoring ODK doivent respecter le template xlxs de monitoring fourni avec ce dépôt. Ce template crée des formulaires dont les noms de champs respectent la structure de donnée destination de la base de données GeoNature (pour les champs générique des visites et observations). Tous les champs qui ne "match" pas ces correspondances seront poussés comme champ spécifique au format json.

Actuellement, seul les champs suivants sont configurables et peuvent être différents de la structure défini par le template xlsx:

- Au niveau de la visite :

  - le nom du "noeud" de la boucle (repeat) contenant les observateurs. Champ `observers_repeat`
  - le nom du champ contenant l'id_role du noeud "observers_repeat". Champ `id_observer`
  - le nom du champ contant le commentaire. Champ `comments`
  - le nom du champ contenant le média. Champ `media`
  - le type média. Champ `media_type`

- Au niveau de l'observation :
  - le nom du "noeud" de la boucle repeat contenant les observations. Champ `observations_repeat`
  - le nom du champ contant le commentaire. Champ `comments`
  - le nom du champ contenant le média. Champ `media`
  - le type média. Champ `media_type`

Amélioration : rendre tous les champs paramétrables...

exemple protocole STOM (cette configuration correspond à la configuration par défaut et n'a pas besoin d'être spécifiée

```

```

[STOM]
[STOM.VISIT] # nom du champ commentaire de la visite (optionnel, defaut comments_visit)
comments = "comments_visit" # nom du champ média de la visite (optionnel, defaut medias_visit)
media = "medias_visit" # nom du du noeud d'accès au tableau d'observateur (optionnel, defaut 'observer')
observers_repeat = 'observer' # nom de la clé contenant l'id_role du noeud "observers_repeat" (optionnel, defaut 'id_role')
id_observer = 'id_role' # type du media (optionnel, defaut "Photo" - valeur possible "Photo", "PDF", "Audio", "Vidéo (fichier)" )
media_type = "Photo"
[STOM.OBSERVATION] # nom du noeud repeat d'accès au tableau d'observations (optionnel, defaut : 'observations')
observations_repeat = "observations" # nom du champ commentaire de l'observation (optionnel, defaut comments_observation)
comments = "comments_observation" # nom du champ média de la visite (optionnel, defaut medias_visit)
media = "medias_observation" # type du media (optionnel, defaut "Photo" - valeur possible "Photo", "PDF", "Audio", "Vidéo (fichier)" )
media_type = "Photo"

````

## Templates et exemples de formulaires

Un template de formulaire au format XLSX est fourni dans le dossier ``/form_template``. Il permet d'avoir la structure de base de définition d'un formulaire compatible avec le module Monitoring de GeoNature et la structure de données attendue par ODK2GN.

Des exemples fonctionnels de formulaires sont aussi disponibles dans les dossiers d'exemples de protocoles de Monitoring :

- https://github.com/PnX-SI/protocoles_suivi/tree/master/stom
- https://github.com/PnX-SI/protocoles_suivi/tree/master/chiro

## Commandes

Avant de lancer une commande, il faut s'assurer d'être dans le virtualenv de l'application GeoNature et dans le dossier de l'application :

```sh
cd  <path_vers_odk2gn>
source <path_vers_gn>/backend/venv/bin/activate
````

### Synchronisation des données de ODK vers GeoNature

Permet de récupérer les données saisies dans ODK central via ODK collect ainsi que les médias associés :

```sh
synchronize <MON_CODE_MODULE> --form_id=<ODK_FORM_ID> --project_id=<ODK_PROJECT_ID>
```

### Mise à jour du formulaire ODK

Publie sur ODK central une nouvelle version du formulaire avec une mise à jour des médias à partir des données de GeoNature. Les données envoyées sont :

- liste des sites
- liste des taxons
- liste des observateurs
- liste des jeux de données
- liste des nomenclatures

```sh
upgrade_odk_form <MON_CODE_MODULE> --form_id=<ODK_FORM_ID> --project_id=<ODK_PROJECT_ID>
```

Des options permettent de ne pas synchroniser certains types de données :

- `--skip_taxons` : ne pas générer le fichier des taxons
- `--skip_observers` : ne pas générer le fichier des observateurs
- `--skip_jdd` : ne pas générer le fichier des jeux de données
- `--skip_sites` : ne pas générer le fichier des sites
- `--skip_nomenclatures` : ne pas générer le fichier des nomenclatures
