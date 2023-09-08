CHANGELOG
=========

1.0.0 (08-09-2023)
------------------

Refactorisation, consolidation et enrichissement du module par @Xav18.
Compatible avec GeoNature version 2.12.0.
Necessite python > 3.10 (Debian 11 minimum).

**🚀 Nouveautés**

- Ajout de gestion des sites (en plus des visites et observations
- Mise à jour des templates de formulaires
- Packaging du module en tant que module GeoNature
- Création de la table `odk2gn.t_odk_forms` permettant de lister les projets ODK synchronisés
- Administration de cette table directement dans le module Admin de GeoNature
- Endpoint pour pouvoir brancher d'autres modules de GeoNature
- Création d'un exemple de modules GeoNature (https://github.com/PnEcrins/odk2gn_flore_prioritaire)
- Mise en place de tests unitaires
- Lancement automatique des tests avec des Github actions

**🐛 Corrections**

**⚠️ Notes de version**

Si vous mettez à jour ODK2GN, vous devez : 
- l'installer à nouveau car c'est un module ...
- lancer la migration Alembic pour créer la table `odk2gn.t_odk_forms` et les permissions associées

0.1.0 - Christophe (09-08-2023)
-------------------------------

Première version fonctionnelle du module suite au workshop des parcs nationaux et de l'OFB en décembre 2022.
