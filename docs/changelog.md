CHANGELOG
=========

1.2.0 - (19-09-2025)
--------------------


**🚀 Nouveautés**

- Possibilité d'utiliser ODK2GN sans avoir le module monitoring installé
- Compatibilité avec monitoring 1.x (sites multi-modules)

**⚠️ Notes de version**

- En lien avec les évolutions de monitoring 1.x et la possibilité d'associer un site à plusieurs modules via la notion de type de site, des modifications sont à faire dans vos formulaires ODK. Ceux-ci doivent un integrer un champs "type_site". Voir le fichier d'exemple "ODK-Form-GeoNature-monitoring-Template-With-Site-Creation.xlsx". Une valeur par défaut peut être passé si le module a un seul type de site.
- Ajout des champs suivants dans la config : 
  NB : tout ces paramètres sont facultatifs et ont des valeurs par défaut (celle des nom des champs dans le formulaire XLK ODK d'exemple). Elles sont à modifier uniquement si vous avez changé les noms des champs dans le formulaire XLS.
  - `create_visit` : nom du champs qui contrôle si l'utilisateur veut créer ou non des visite dans le formulaire
  - `types_site` : nom du champs renseignant le type de site
  - `id_digitiser` : nom du champs renseignant le digitiser
  - `medias_site` : nom du champs renseignant la photo du site. Si vous soihaitez pouvoir ajouter autre chose que des photos, veuillez modifier le paramètre `media_type`.


1.1.0 (15-04-2025)
------------------

**🚀 Nouveautés**

- Compatibilité avec GeoNature 2.14 et Monitoring 0.7.X
- Possibilité d'utiliser le module sans avoir le module Monitoring installé

**⚠️ Notes de version**

- installer le module ODK2GN comme un module GeoNature : 
```
  geonature install-gn-module <chemin vers odk2gn> --build=false
```
Vous devrez ensuite associer des permissions au module :

Pour donner tous les droits au groupe admin : 
```
geonature permissions supergrant --group --nom "Grp_admin" --yes
```

- Supprimez les champs `data` de la configuration Monitoring de vos modules dans le fichier `odk2gn_config.toml`
- La gestion de la création des sites est désormais contrôlée à deux niveaux dans la configuration du module :
Au niveau de la section du module, le booléen `can_create_site` contrôle si le module autorise la création de site : 

```
[[modules]]
    module_code = "suivi_nardaie"
    # booléen indiquant la création de sites
    can_create_site=true
```

et au niveau de la section `SITE`, le champs `create_site` (str) indique quel est le nom du champs dans le formulaire ODK qui offre la possibilité de choisir un site existant ou d'en créer un. Ce champs du formulaire ODK doit renvoyer un booléen
```
[[modules]]
    module_code = "suivi_nardaie"
    # booléen indiquant la création de sites
    can_create_site=true
    [modules.SITE]
        # non du champs qui demande à l'utilisateur s'il veut créer un site ou en selectionner un existant
        # compatible uniquement avec can_create_site=true
        create_site = "create_site"
```

Note de version:

La valeur par defaut du champs `base_site_name` et désormais `base_site_name`, anciennement `site_name`. Veuillez changer le nom du champs dans vos formulaire ODK ou modifierr votre configuration


1.0.0 (08-09-2023)
------------------

Refactorisation, consolidation et enrichissement du module par @Xav18.
Compatible avec GeoNature version 2.12.0.
Necessite python > 3.10 (Debian 11 minimum).

**🚀 Nouveautés**

- Ajout de la possibilité de créer des sites (en plus des visites et observations)
- Mise à jour des templates de formulaires
- Packaging du module en tant que module GeoNature
- Création de la table `odk2gn.t_odk_forms` permettant de lister les projets ODK synchronisés
- Administration de cette table directement dans le module Admin de GeoNature
- Possibilité de lancer les synchronisation automatiquement via Celery-beat
- Mise en place de tests unitaires
- Possibilité de créer des "sous-modules" de synchronisation basé sur d'autre module GeoNature que monitoring. Voir : https://github.com/PnEcrins/odk2gn_flore_prioritaire

**🐛 Corrections**

**⚠️ Notes de version**

Si vous mettez à jour ODK2GN, vous devez : 
- le désinstaller : `pip uninstall odk2gn`
- l'installer à nouveau car c'est un module maintenant un module GeoNature 
- lancer la migration Alembic pour créer la table `odk2gn.t_odk_forms` et les permissions associées

0.1.0 - Christophe (09-08-2023)
-------------------------------

Première version fonctionnelle du module suite au workshop des parcs nationaux et de l'OFB en décembre 2022.
