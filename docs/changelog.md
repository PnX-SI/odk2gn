CHANGELOG
=========


1.1.0
-----

- Compatibilité avec GeoNature 2.15 (taxhub v2 et monitoring 1.0.0 (?))

Note de version : 

- installer le module ODK2GN comme un module geonature : 

```
  geonature install-gn-module <chemin vers odk2gn> --build=false
```
Vous devrez ensuite associer des permssions au module :

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
