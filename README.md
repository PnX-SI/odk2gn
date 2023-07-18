# ODK Central to GeoNature

ODK2GN est un module python utilisant les modèles de GeoNature pour intégrer des données depuis l'API d'ODK Central vers la base de données de GeoNature, en utilisant pyodk.

Il permet actuellement d'importer des données collectées avec ODK vers le module Monitoring de GeoNature et de mettre à jour les listes de valeurs du formulaire ODK en fonction des données de la base de données GeoNature, en se basant sur les fichiers de configuration du module Monitoring.

Développé dans le cadre du workshop ODK des parcs nationaux de France et de l'OFB (Décembre 2022) : https://geonature.fr/documents/2022-12-PNX-OFB-Workshop-ODK.pdf

## Architecture

![Architecture](docs/img/archi_global.jpeg)

## Installation

Bien qu'indépendant, l'installation de ce module se fait dans l'environnement de GeoNature.

```sh
# Activation du virtual env de GeoNature
source <path_vers_gn>/backend/venv/bin/activate

# Installation des modules : 
se mettre dans le dossier où figure le fichier setup.py du module, puis dans le terminal:
pip install -e . -r requirements.txt
Faire cette manipulation à chaque fois qu'on crée un nouveau module.
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

Actuellement seul les niveaux "visites" et "observations" sont implémentés. Il n'est pas possible de créer des sites à partir des formulaires ODK.

Les formulaire monitoring ODK doivent respecter le template xlsx de monitoring fourni avec ce dépôt. Ce template crée des formulaires dont les noms de champs respectent la structure de donnée destination de la base de données GeoNature (pour les champs générique des visites et observations). Tous les champs qui ne "match" pas ces correspondances seront poussés comme champ spécifique au format json.

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

Exemple protocole STOM (cette configuration correspond à la configuration par défaut et n'a pas besoin d'être spécifiée).

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

Un template de formulaire au format XLSX est fourni dans le dossier ``/odk_template_form``. Il permet d'avoir la structure de base de définition d'un formulaire compatible avec le module Monitoring de GeoNature et la structure de données attendue par ODK2GN.

Des exemples fonctionnels de formulaires sont aussi disponibles dans les dossiers d'exemples de protocoles de Monitoring :

- https://github.com/PnX-SI/protocoles_suivi/tree/master/chiro/odk_form
- https://github.com/PnX-SI/protocoles_suivi/tree/master/stom/odk_form

## Commandes

Avant de lancer une commande, il faut s'assurer d'être dans le virtualenv de l'application GeoNature et dans le dossier de l'application :

```sh
cd  <path_vers_odk2gn>
source <path_vers_gn>/backend/venv/bin/activate
````

### Synchronisation des données de ODK vers GeoNature

Permet de récupérer les données saisies dans ODK central via ODK collect ainsi que les médias associés.

De façon a distinguer les données intégrées en base, de celles non traitées le module opère une modification de la métadonnées `reviewState`
Une fois une soumission intégrée en base son `reviewState` est modifiée en `approuved`. Si l'insertion dans GeoNature ne peut se faire la soumission est marquée en `hasIssue`. De cette façon l’administrateur de données peut traiter manuellement la données problèmatique via enketo.

```sh
synchronize monitoring <MON_CODE_MODULE> --form_id=<ODK_FORM_ID> --project_id=<ODK_PROJECT_ID>
```

### Mise à jour du formulaire ODK

Publie sur ODK central une nouvelle version du formulaire avec une mise à jour des médias à partir des données de GeoNature. Les données envoyées sont :

- liste des sites
- liste des taxons
- liste des observateurs
- liste des jeux de données
- liste des nomenclatures

```sh
upgrade_odk_form monitoring <MON_CODE_MODULE> --form_id=<ODK_FORM_ID> --project_id=<ODK_PROJECT_ID>
```

Des options permettent de ne pas synchroniser certains types de données :

- `--skip_taxons` : ne pas générer le fichier des taxons
- `--skip_observers` : ne pas générer le fichier des observateurs
- `--skip_jdd` : ne pas générer le fichier des jeux de données
- `--skip_sites` : ne pas générer le fichier des sites
- `--skip_nomenclatures` : ne pas générer le fichier des nomenclatures

**Module flore prioritaire**

Le formulaire flore prioritaire ODK doit respecter le template xlsx. Ce template crée des formulaires dont les noms de champs respectent la structure de donnée destination de la base de données GeoNature, en créeant des objets zone de prospection et aire de présence, et en les poussant à la base. Tous les champs qui ne "match" pas ces correspondances seront poussés comme champ spécifique au format json.

## Commandes

Avant de lancer une commande, il faut s'assurer d'être dans le virtualenv de l'application GeoNature et dans le dossier de l'application :

```sh
cd  <path_vers_odk2gn>
source <path_vers_gn>/backend/venv/bin/activate
````

### Synchronisation des données de ODK vers GeoNature

Permet de récupérer les données saisies dans ODK central via ODK collect ainsi que les médias associés.

De façon a distinguer les données intégrées en base, de celles non traitées le module opère une modification de la métadonnées `reviewState`
Une fois une soumission intégrée en base son `reviewState` est modifiée en `approuved`. Si l'insertion dans GeoNature ne peut se faire la soumission est marquée en `hasIssue`. De cette façon l’administrateur de données peut traiter manuellement la données problèmatique via enketo.

```sh
synchronize flore-prio --form_id=<ODK_FORM_ID> --project_id=<ODK_PROJECT_ID>
```

### Mise à jour du formulaire ODK

Publie sur ODK central une nouvelle version du formulaire avec une mise à jour des médias à partir des données de GeoNature. Les données envoyées sont :

```sh
upgrade-odk-form flore-prio --form_id=<ODK_FORM_ID> --project_id=<ODK_PROJECT_ID>
````

En effet, les commandes synchronize et update-odk-form sont utilisés pour pousser à la base les données ou mettre à jour la base pour tout module