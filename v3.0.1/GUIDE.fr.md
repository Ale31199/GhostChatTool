# GhostChatTool v3.0.1 — Guide français

[English — par défaut](GUIDE.en.md) · [Italiano](GUIDE.it.md) · [Español](GUIDE.es.md) · Français · [Deutsch](GUIDE.de.md)

## Quelle version ?

La v3.0.1 surveille les journaux locaux : **aucun navigateur ouvert n'est nécessaire**. Ce n'est ni le sélecteur manuel v1, ni l'extension v4. Le code d'origine est conservé ; ce paquet ajoute des commandes et des guides. Les lanceurs désactivent le rechargement automatique expérimental et les nudges. Si la liste reste ancienne, quittez complètement l'application et rouvrez-la vous-même.

C'est un contournement expérimental non officiel, sans affiliation à OpenAI. Il ne garantit pas la disparition de toutes les conversations fantômes, même après réouverture. Il répare uniquement lorsqu'une même ligne de journal contient l'ID de la conversation et `conversation_deleted` ou `conversation deleted`. Sans cet événement, aucune réparation. Il ne vérifie pas directement le serveur et ne réalise pas deux contrôles serveur.

## Préparation et installation

Il faut Windows 10/11, Python 3.10+ accessible par `py` ou `python`, Windows PowerShell et `%USERPROFILE%\.codex\sqlite\codex-dev.db`. Aucun paquet Python supplémentaire ni identifiant n'est requis. Extrayez entièrement le ZIP avant d'exécuter les fichiers.

Si la v3.0.1 fonctionne déjà, n'installez pas une deuxième copie. Pour migrer, arrêtez l'ancienne version et désactivez son démarrage automatique selon ses instructions. Windows + R, `shell:startup`, ouvre le dossier de démarrage. Ne supprimez pas d'entrées inconnues ni `.codex`. L'installateur refuse une entrée GhostChat existante, un processus de surveillance actif ou un dossier cible existant. Il ne désinstalle pas automatiquement la v4 ni les extensions.

1. Ouvrez `GUIDE.html` pour choisir la langue. `DRY_RUN.cmd` affiche les candidats sans modifier lui-même la base. Une autre instance active peut toujours écrire : arrêtez-la pour un test entièrement en lecture seule.
2. Lancez `INSTALL.cmd`, lisez l'avertissement et saisissez `INSTALL`. Installation dans `%LOCALAPPDATA%\GhostChatTool-v3.0.1`, création de `GhostChatTool v3.0.1.lnk` au démarrage de l'utilisateur et lancement de la surveillance masquée.
3. Dans le **dossier installé**, utilisez `STATUS.cmd`, `STOP.cmd` et `START.cmd`. Pas de droits administrateur. Ce n'est pas un service : Windows et la session utilisateur doivent rester actifs. STOP ne désactive pas le prochain démarrage à la connexion.

En cas d'erreur, vérifiez l'état avant de supposer que l'installation fonctionne. Ne contournez pas la politique de sécurité de votre organisation.

## Tester une conversation jetable

1. Créez une conversation de test hors Projects et vérifiez sa présence sur le PC.
2. Supprimez uniquement ce test depuis le téléphone. La suppression sur le serveur est définitive. Gardez l'application du PC connectée.
3. Dans `STATUS.cmd`, recherchez une nouvelle date de réparation et un nombre de suppressions supérieur à zéro. Le manifeste privé identifie la conversation réparée. Une ancienne réparation ne prouve rien pour ce test.
4. Si elle reste visible, quittez entièrement l'application, y compris ses processus en arrière-plan, puis rouvrez-la depuis Démarrer. Aucun bouton Recharger n'est nécessaire ; GhostChat ne force pas la fermeture.
5. Sans nouvelle réparation, arrêtez la surveillance, fermez l'application et exécutez `DRY_RUN.cmd`. Sans événement valable, l'entrée reste intacte. `REPAIR_ONCE.cmd` permet une réparation ponctuelle des candidats confirmés, application et surveillance fermées. Rouvrez ensuite l'application et utilisez `START.cmd`.

La vérification a normalement lieu toutes les trois secondes et la recherche des journaux toutes les quinze secondes environ, **sans garantie de délai**. L'application peut ne jamais produire l'événement nécessaire. Ne supprimez pas d'autres conversations importantes pour essayer.

## Sauvegardes, restauration et désinstallation

Sauvegardes : `%USERPROFILE%\.codex\sqlite\ghostchat-backups`. État, journaux et manifestes privés : `%USERPROFILE%\.codex\sqlite\ghostchat-patch`. Jusqu'à 20 sauvegardes sont conservées après les réparations, dans un emplacement partagé avec les versions anciennes. Conservez ailleurs les copies importantes.

`RESTORE.cmd` arrête la surveillance de ce paquet, exige la fermeture complète de l'application et demande `RESTORE`. Il restaure la sauvegarde la plus récente de **toute la base locale**, pas une conversation isolée, et crée une sauvegarde préalable. D'autres modifications locales peuvent être annulées. La surveillance reste arrêtée, mais le démarrage à la connexion demeure actif ; un redémarrage peut réappliquer la réparation. Pour le désactiver pendant la récupération, lancez d'abord `UNINSTALL.cmd`, puis restaurez depuis les fichiers conservés.

`UNINSTALL.cmd` arrête la surveillance et supprime uniquement le raccourci de démarrage de ce paquet. Programme, base, journaux et sauvegardes sont conservés. Il n'annule pas les réparations et ne désinstalle pas les autres versions ou extensions.

## Limites et confidentialité

Les lanceurs vérifient les colonnes avant le démarrage ; l'exclusion des Projects dans le code d'origine dépend de `project_id`. Aucun arrêt sûr universel n'est garanti lors de futurs changements de schéma. La sauvegarde précède la réparation ; `PRAGMA integrity_check` intervient après validation de la modification. Il ne vérifie pas le serveur et ne garantit pas une annulation automatique. Cessez d'utiliser l'outil si une mise à jour casse la compatibilité.

Aucune lecture/exportation de cookies, jetons ou `auth.json`, aucun appel direct aux API privées, aucune modification/injection dans l'exécutable. Les journaux, manifestes et sauvegardes peuvent contenir des données privées : ne les partagez pas sans les expurger. La publication contient seulement code, guides et tests synthétiques. Voir `README.md` et `TEST_REPORT.md` pour les limites et les contrôles réalisés.
