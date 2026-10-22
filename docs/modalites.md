# Six natures

Chaque cas déclare une nature. La nature dit ce qu'il faut avoir sous les yeux pour juger, et ce qu'une prédiction est en train d'évaluer. Le dépôt ne lance pas de modèle. Une sortie de modèle se dépose comme n'importe quelle autre prédiction. Elle ne devient pas un verdict `revu`.

## Déterministe

Les pièces sont dans le HTML ou le CSS, et la méthode ferme le test par une vérification qui ne demande pas d'interpréter un sens. Exemples du lot : doctype, langue présente, titre présent, intitulé de lien présent, contraste d'un texte dont les deux couleurs sont déclarées sur le même élément.

## Pertinence

Il faut comprendre ce que le texte, l'alternative ou le titre veulent dire, et le rapporter aux conditions du test. Deux personnes peuvent conclure autrement. Si les deux lectures restent défendables, le cas est `non_tranche`.

## Vision

Le HTML ne suffit pas. Une capture PNG, faite avec un navigateur et une version nommés, montre les pixels jugés. Le lot contient le texte peint dans une image : la feuille de style ne porte pas la couleur du texte.

## Geste

Il faut agir sur la page : focus clavier, zoom, redimensionnement, envoi d'un formulaire. La capture montre l'état après le geste. Le viewport ou le zoom est noté. Le lot contient la prise de focus.

## Restitution

Il faut une technologie d'assistance, dans la combinaison que l'on a réellement lancée. Un cas `revu` joint la transcription et nomme le produit, la version, la langue et le système. Le lot ne contient qu'un brouillon : la transcription d'exemple ne peut pas être promue.

## Document

Le cas porte sur un fichier bureautique ou un PDF, pas sur une page HTML. Le lot semence n'en contient pas. Une contribution dépose le fichier, le test visé et le motif. Le scoreur le traitera comme les autres cas dès qu'il sera `revu`.
