CHANGELOG
=========


1.2.0 - unreleased
-------------------

1.1.0 (14-04-2024)
-------------------

- Compatibilité avec GeoNature 2.14 et monitoring 0.7.X
- Possibilité d'utiliser le module sans avoir le module monitoring d'installé

Note de version : 

- installer le module ODK2GN comme un module geonature : 
```
  geonature install-gn-module <chemin vers odk2gn> --build=false
```
- Supprimez les champs `data` de la configuration de vos modules dans le fichier `odk2gn_config.toml`
- La gestion de la création des sites / visites / observations change. Le fait de pouvoir créer des sites étaient controlé par un paramètre de configuration `create_site` qui pointait vers le nom d'un champs du formulaire ODK. Ce sont désormais 3 booléens qui controle ça au niveau de la configuration ODK2GN de chaque sous module (voir le fichier d'exemple `odk2gn_config.toml.example`). Par défault les valeurs sont à `True` (bien veiller à passer les bonne valeur si vous voulez désactiver la création d'entitité à un niveau)

```
    create_site=false
    create_visit=true
    create_observation=true
```


Vous devrez ensuite associer des permissions au module :

Pour donner tous les droits aux groupe admin : 
`geonature permissions supergrant --group --nom "Grp_admin" --yes
`


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
