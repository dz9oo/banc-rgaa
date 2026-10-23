# Contribuer

Une contribution utile est un cas, un protocole, ou un correctif des outils. Le plus court chemin est un cas.

## La branche main

Une modification de `main` entre par une pull request. Le propriétaire du dépôt la fusionne. Un push direct, un force-push et la suppression de `main` sont refusés. La fusion attend le contrôle `valider`, sur une branche à jour de `main`.

Une contribution extérieure part d'un fork. Elle ne donne pas le droit d'écriture sur ce dépôt.

## Un cas

1. Choisir un test du RGAA 4.1.2 dans `referentiel/rgaa-4.1.2/index.json`.
2. Copier un dossier voisin dans `cas/rgaa-4.1.2/<test>/<slug>/`.
3. Écrire une page minimale. Pas de site client, pas de donnée personnelle, pas de texte copié depuis un service réel.
4. Remplir `cas.json`. Le motif explique le verdict à partir du test officiel, en 80 à 2 000 caractères. L'URL `methode` est celle de ce test.
5. Laisser `statut` à `brouillon`.
6. Lancer `python3 outils/valider.py`.
7. Régénérer la page d'accueil et le site : `python3 outils/couverture.py` puis `python3 outils/site.py`.

Quand le test le permet, proposer la paire : un cas conforme et un cas non conforme. Si deux lectures restent défendables après lecture de la méthode, le verdict est `non_tranche` et `desaccords` contient les deux lectures.

Le lot semence, présent à l'ouverture, a été relu sur la page de chaque test le 2026-10-22. Ensuite, le passage à `revu` se fait dans une pull request, par une personne qui n'a pas écrit le cas. Le message dit : « relu sur le test X.Y.Z le AAAA-MM-JJ ». Le champ `relecture` porte cette date.

## Un protocole

Un fichier `protocoles/rgaa-4.1.2/<test>.md`, avec le front matter décrit dans `schema/protocole.schema.json`. Trois titres : `Environnement`, `Ce qui se tranche`, `Pièges`. La carte ne remplace pas la méthode : elle dit comment le banc s'en sert, et elle nomme les cas du dépôt. Puis :

```bash
python3 outils/indexer.py
python3 outils/valider.py
```

## Une prédiction

Pour évaluer une lecture, humaine ou outillée, déposer un JSON :

```bash
python3 outils/scorer.py exemples/prediction-parfaite.json
```

Le format est dans `schema/prediction.schema.json`. Une prédiction absente sur un cas tranché est un silence. Elle ne compte pas comme un désaccord. Sur un cas `non_tranche`, s'abstenir est le comportement mesuré.

## Licences des contributions

Les pages, les motifs et les protocoles sont contribués sous Licence Ouverte 2.0. Les scripts sont contribués sous MIT ou Apache-2.0, au choix de la personne qui contribue. Voir `LICENSES/`.

## Ce qui ne part pas

Le validateur refuse un `revu` de restitution dont la transcription contient encore la balise `EXEMPLE`. Une passe réelle nomme la technologie d'assistance, sa version, sa langue et son système.

Les intitulés officiels vivent dans `referentiel/rgaa-4.1.2/criteres.json`. On ne les réécrit pas à la main. On met à jour le relevé, `SOURCE.md`, puis `python3 outils/indexer.py`.
