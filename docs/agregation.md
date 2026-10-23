# Agrégation et taux

`outils/agregar.py` applique ces règles à la grille d'un échantillon. Il ne lit pas le HTML et il n'audite pas les pages. La personne qui constitue l'échantillon déclare le périmètre et les relevés. Chaque relevé cite un cas de même test et de même verdict. Seul un cas `revu` couvre le test.

## Page

Pour un critère dont chaque test a, sur la page, un relevé qui cite un cas `revu` :

- un relevé non conforme rend le critère non conforme sur cette page ;
- un relevé non tranché laisse le critère non tranché ;
- si tous les relevés sont non applicables, le critère est non applicable sur cette page ;
- sinon, s'il n'y a ni échec ni cas non tranché, le critère est conforme sur cette page.

## Processus

Si deux pages portent le même `processus` et que le critère est non conforme sur l'une, il devient non conforme sur les autres pages du processus où il était conforme. Une page où le critère est non applicable le reste.

## Échantillon

Le critère de l'échantillon reprend l'échec dès qu'une page applicable est non conforme. Il est conforme si au moins une page le rend conforme et qu'aucune ne le rend non conforme ou non tranché. Il est non applicable si toutes les pages le sont.

## Couverture

Un critère du périmètre n'entre dans `criteres` que lorsque chacun de ses tests a, sur chaque page, un relevé qui cite un cas `revu`. Sinon il est ouvert. Un relevé qui cite un brouillon est conservé et ne couvre pas le test. Le motif du taux nomme les critères ouverts.

## Taux

Le taux est le nombre de critères conformes divisé par le nombre de critères applicables (conformes et non conformes), exprimé en pourcentage arrondi au dixième, moitié vers le haut. Les critères non applicables ne sont pas au dénominateur.

Le taux reste `null` tant qu'un critère du périmètre est ouvert ou non tranché, ou tant qu'aucun critère du périmètre n'est applicable. Un taux vide est un état normal du lot semence : l'échantillon `vitrine` a des critères applicables qui n'ont pas encore tous leurs tests couverts par un cas `revu`.

Cette règle sert à ne pas publier un pourcentage sur une grille trouée. Elle reprend le principe du taux RGAA : les critères applicables, pas les tests, et un échec sur une page de l'échantillon suffit. Le détail opératoire du référentiel reste celui de la méthode officielle.
