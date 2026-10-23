# Banc d'essai RGAA

Cas figés, protocoles et échantillon pour évaluer un audit au RGAA 4.1.2. Le banc sert à une personne qui audite à la main, à qui écrit un outil, et à qui mesure un modèle de texte ou de vision.

La méthode officielle donne 106 critères et 258 tests. Elle explique le geste. Elle ne publie pas une page dont le verdict de chaque test aurait déjà été revu. Ce dépôt commence à combler ce trou, test par test, avec des pages minimales et un motif.

## Ce que ce dépôt est

Trois couches, et un contrat de score.

- Un **cas** est une page, parfois une capture ou une transcription, qui exerce un seul test. Le fichier `cas.json` porte le verdict, le motif et la nature du jugement.
- Un **protocole** dit comment vérifier ce test dans le banc : l'environnement, ce qu'une machine peut établir, ce qu'une personne tranche, les pièges fréquents.
- Un **échantillon** assemble quelques pages d'un mini-service. Le taux n'est publié que lorsque chaque critère du périmètre a un relevé complet.
- Le **scoreur** compare une liste de prédictions aux cas `revu`. La même liste sert pour une grille humaine, un outil, ou un modèle.

Un verdict `revu` est la lecture des contributrices et contributeurs. Il est relié à l'URL du test officiel et à un motif écrit. Ce n'est pas une copie corrigée de l'État.

## Ce que ce dépôt laisse à la DINUM

La méthode reste sur [accessibilite.numerique.gouv.fr](https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/). [Ara](https://ara.numerique.gouv.fr/) reste l'outil de saisie des audits. La grille ODS reste le modèle vide de relevé. Le banc ne signe pas une déclaration d'accessibilité et ne calcule pas le taux d'un site en ligne.

## État de la couverture

<!-- couverture:debut -->
| Indicateur | Nombre |
| --- | ---: |
| Tests du RGAA 4.1.2 | 258 |
| Critères | 106 |
| Tests avec un protocole | 36 |
| Cas revus | 33 |
| Cas déterministes revus | 13 |
| Cas de pertinence revus | 17 |
| Cas de vision revus | 1 |
| Cas de geste revus | 2 |
| Cas de restitution revus | 0 |
| Cas document revus | 0 |
| Cas brouillons | 28 |
| Cas revus non tranchés | 2 |
| Échantillons | 1 |
| Échantillons avec un taux publié | 0 |
<!-- couverture:fin -->

Le tableau est produit par `python3 outils/couverture.py`. Il compte les cas `revu`. Un brouillon reste dans le dépôt et hors de l'accord. La plupart des 258 tests n'ont encore ni protocole ni cas : c'est le travail de contribution.

## Lire un cas

Les cas sont dans `cas/rgaa-4.1.2/<test>/<slug>/`. `cas.json` porte le verdict. `page.html` s'ouvre dans un navigateur. Le site statique `site/index.html` reprend le motif, le protocole et le lien vers la page.

Les champs qui comptent : `verdict`, `nature`, `modalites`, `motif`, `methode`, `statut`. Le détail est dans `schema/cas.schema.json`.

## Évaluer une lecture

Déposer un JSON : `outil`, `date`, et `predictions`. Chaque prédiction cite l'identifiant du cas (`6.1.1/cliquez-ici`) et un verdict.

```bash
python3 outils/scorer.py exemples/prediction-parfaite.json
python3 outils/scorer.py exemples/prediction-silencieuse.json
python3 outils/scorer.py ma-lecture.json --seuil 100
```

L'accord se calcule sur les cas `revu` dont le verdict d'or est tranché. Une prédiction absente est un silence : elle n'entre pas au dénominateur et elle n'est pas un désaccord. Un cas `non_tranche` mesure l'abstention. Le trancher quand même n'augmente ni l'accord ni l'erreur. `--seuil 100` quitte le programme avec le code 1 si l'accord des cas tentés est en dessous. Un silence, dénominateur vide, ne déclenche pas ce seuil.

Le dépôt ne fixe pas de seuil pour un outil particulier. L'exemple parfait sert à vérifier le scoreur.

## Six natures

`deterministe`, `pertinence`, `vision`, `geste`, `restitution`, `document`. Le détail, et ce que chaque nature demande comme pièce, est dans [docs/modalites.md](docs/modalites.md).

Le dépôt ne lance pas de modèle. Une sortie de modèle se dépose comme prédiction. Elle ne devient pas un verdict `revu`. Les verdicts `revu` viennent d'une relecture humaine, datée, sur la page du test.

## Échantillons et taux

Les règles tenues par `outils/agregar.py` sont dans [docs/agregation.md](docs/agregation.md). L'échantillon `vitrine` a un taux vide : des critères applicables n'ont pas encore tous leurs tests revus. Des relevés citent des cas encore `brouillon` : ils sont enregistrés et ne couvrent pas le test tant que le cas n'est pas `revu`. Un taux vide est un résultat, pas un oubli de publication.

## Contribuer

Copier un cas, garder `brouillon`, lancer le validateur, ouvrir une pull request. Le passage à `revu` est fait par une autre personne.

```bash
python3 outils/valider.py
```

Le guide est [CONTRIBUTING.md](CONTRIBUTING.md). Le code de conduite est [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Statuts

- `brouillon` : le cas est proposé. Il ne compte pas dans l'accord.
- `revu` : une personne autre que l'auteur a relu le cas sur la page du test, à la date de `relecture`.
- `non_tranche` : deux lectures défendables sont publiées dans `desaccords`. Le cas est un résultat. Il apprend à une lecture automatique à s'abstenir.

## Licences et relevé du référentiel

Les schémas, les scripts, le site et la CI sont sous MIT ou Apache-2.0. Les cas, les protocoles et les motifs sont sous Licence Ouverte 2.0. Les textes sont dans `LICENSES/`.

Les identifiants et les intitulés viennent de `referentiel/rgaa-4.1.2/criteres.json`, relevé DINUM, Licence Ouverte 2.0. La source, le commit et l'empreinte sont dans [referentiel/rgaa-4.1.2/SOURCE.md](referentiel/rgaa-4.1.2/SOURCE.md). L'index dérivé n'ajoute pas de règle de calcul.

## Travaux proches

- [Ara](https://github.com/DISIC/Ara) saisit un audit et produit le rapport. Ara n'analyse pas la page.
- La [grille d'audit ODS](https://accessibilite.numerique.gouv.fr/ressources/kit-audit/) est le modèle vide du relevé.
- [DISIC/RGAA-tests](https://github.com/DISIC/RGAA-tests) publie un texte de méthodologie pour la version 4, sans pages notées.
- [DISIC/rgaa-test-suite](https://github.com/DISIC/rgaa-test-suite) (2017) exerce des composants ARIA du RGAA 3.
- Les [ACT Rules du W3C](https://www.w3.org/WAI/standards-guidelines/act/rules/) fournissent des cas pour des règles WCAG. Une adaptation future devra citer l'URL d'origine. Le lot semence est original.
- [Accorma RGAA Corpus](https://github.com/0SansNom/accorma-rgaa-corpus) publie 1 435 pages notées au niveau du critère, en anglais, pour un article de recherche. Le banc est au niveau du test, en français, ouvert aux contributions, et il distingue la vision, le geste et la restitution.
- [rgaa-a11y-benchmark](https://github.com/yvoolab/rgaa-a11y-benchmark) pose six fragments et un critère WCAG.

## Limites

Aucune transcription réelle de technologie d'assistance n'est encore versée : le cas de restitution est un brouillon. L'échantillon `vitrine` ne publie pas de taux. Le RGAA 5 n'est pas importé : la méthode est encore en rédaction, voir `referentiel/rgaa-5/LISEZMOI.md`. Un cas `revu` peut être corrigé. La pull request explique le changement de verdict.

Les mots-clés du dépôt : `rgaa`, `rgaa-4`, `accessibilite`, `accessibilite-numerique`, `wcag`, `a11y`, `audit`, `corpus`, `banc-dessai`, `cas-de-test`.
