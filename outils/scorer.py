#!/usr/bin/env python3
"""Compare une liste de prédictions aux cas revus."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc

PARFAIT = banc.RACINE / "exemples" / "prediction-parfaite.json"
SILENCIEUX = banc.RACINE / "exemples" / "prediction-silencieuse.json"


def ecrire_exemples() -> None:
    cas = banc.charger_cas()
    banc.ecrire_json(PARFAIT, banc.exemple_parfait(cas))
    banc.ecrire_json(SILENCIEUX, banc.exemple_silencieux())


def exemples_a_jour() -> list[str]:
    erreurs = []
    cas = banc.charger_cas()
    if not PARFAIT.is_file() or banc.lire_json(PARFAIT) != banc.exemple_parfait(cas):
        erreurs.append("exemples/prediction-parfaite.json n'est pas à jour")
    if not SILENCIEUX.is_file() or banc.lire_json(SILENCIEUX) != banc.exemple_silencieux():
        erreurs.append("exemples/prediction-silencieuse.json n'est pas à jour")
    return erreurs


def noter_fichier(chemin: Path, seuil: float | None) -> int:
    try:
        donnees = banc.lire_prediction(chemin)
    except (OSError, ValueError, json_error()) as exc:
        print(exc)
        return 2
    resultat = banc.resultat_score(
        donnees["outil"], donnees["date"], donnees["predictions"], banc.charger_cas()
    )
    print(banc.texte_score(resultat))
    print(json_module().dumps(resultat, ensure_ascii=False, indent=2))
    return banc.code_seuil(resultat, seuil)


def json_error():
    import json

    return json.JSONDecodeError


def json_module():
    import json

    return json


def auto_test() -> int:
    erreurs = exemples_a_jour()
    cas = banc.charger_cas()
    parfait = banc.resultat_score("lecture-parfaite", "2026-10-22", banc.exemple_parfait(cas)["predictions"], cas)
    if parfait["accord"] != 100 or parfait["silences"] != 0 or parfait["tranchages"] != 0:
        erreurs.append(f"lecture parfaite inattendue : {parfait['accord']} silences {parfait['silences']}")
    if parfait["abstentions"] != parfait["non_tranches"]:
        erreurs.append("la lecture parfaite doit s'abstenir sur chaque cas non tranché")
    vide = banc.resultat_score("lecture-vide", "2026-10-22", [], cas)
    if vide["accord"] is not None or vide["silences"] != vide["or_tranches"]:
        erreurs.append("le silence n'est pas lu comme un dénominateur vide")
    if banc.code_seuil(vide, 100) != 0:
        erreurs.append("un silence ne doit pas échouer au seuil")
    tranches = [entree for entree in cas if entree["statut"] == "revu" and entree["verdict"] != "non_tranche"]
    if not tranches:
        erreurs.append("aucun cas revu tranché")
    else:
        cible = tranches[0]
        inverse = "conforme" if cible["verdict"] != "conforme" else "non_conforme"
        faux = banc.resultat_score(
            "lecture-fausse",
            "2026-10-22",
            [{"cas": cible["id"], "verdict": inverse}],
            cas,
        )
        if faux["accord"] == 100 or banc.code_seuil(faux, 100) != 1:
            erreurs.append("une prédiction fausse devrait rester sous le seuil 100")
    ouverts = [entree for entree in cas if entree["statut"] == "revu" and entree["verdict"] == "non_tranche"]
    if ouverts:
        force = banc.resultat_score(
            "lecture-forcee",
            "2026-10-22",
            [{"cas": ouverts[0]["id"], "verdict": "conforme"}],
            cas,
        )
        if force["tranchages"] != 1 or force["accords"] != 0:
            erreurs.append("trancher un cas non tranché ne doit pas entrer dans l'accord")
    if erreurs:
        print("\n".join(erreurs))
        return 1
    print("Scoreur : ok.")
    return 0


def main() -> int:
    if "--ecrire-exemples" in sys.argv:
        ecrire_exemples()
        print("Exemples écrits.")
        return 0
    if "--auto-test" in sys.argv:
        return auto_test()
    arguments = [argument for argument in sys.argv[1:] if not argument.startswith("--")]
    seuil = None
    if "--seuil" in sys.argv:
        seuil = float(sys.argv[sys.argv.index("--seuil") + 1])
    if len(arguments) != 1:
        print("Usage : python3 outils/scorer.py PREDICTION.json [--seuil 100]")
        return 2
    return noter_fichier(Path(arguments[0]), seuil)


if __name__ == "__main__":
    sys.exit(main())
