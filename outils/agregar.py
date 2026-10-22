#!/usr/bin/env python3
"""Recalcule les critères et le taux d'un échantillon à partir de ses relevés."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc


def ecrire() -> None:
    ech = banc.lire_json(banc.CHEMIN_ECHANTILLON)
    calcul = banc.agreger(ech, banc.charger_index())
    ech["criteres"] = calcul["criteres"]
    ech["taux"] = calcul["taux"]
    ech["taux_motif"] = calcul["taux_motif"]
    banc.ecrire_json(banc.CHEMIN_ECHANTILLON, ech)


def auto_test() -> int:
    index = {
        "tests": [
            {"id": "1.1.1", "critere": "1.1"},
            {"id": "1.1.2", "critere": "1.1"},
            {"id": "2.1.1", "critere": "2.1"},
            {"id": "3.1.1", "critere": "3.1"},
        ]
    }

    def ech(releves, perimetre, pages=None):
        if pages is None:
            pages = [
                {"id": "a", "fichier": "a.html", "motifs": ["accueil"]},
                {"id": "b", "fichier": "b.html", "motifs": ["contact"]},
            ]
        return {"pages": pages, "perimetre": perimetre, "releves": releves}

    complet = ech(
        [
            {"page": "a", "test": "2.1.1", "verdict": "conforme", "cas": "x"},
            {"page": "b", "test": "2.1.1", "verdict": "conforme", "cas": "x"},
        ],
        ["2.1"],
    )
    calcul = banc.agreger(complet, index)
    if calcul["taux"] != 100 or calcul["criteres"][0]["verdict"] != "conforme":
        return _echec("un critère conforme partout devrait donner 100")
    echec = ech(
        [
            {"page": "a", "test": "2.1.1", "verdict": "non_conforme", "cas": "x"},
            {"page": "b", "test": "2.1.1", "verdict": "conforme", "cas": "x"},
        ],
        ["2.1"],
    )
    calcul = banc.agreger(echec, index)
    if calcul["criteres"][0]["verdict"] != "non_conforme" or calcul["taux"] != 0:
        return _echec("un échec sur une page devrait invalider le critère")
    incomplet = ech(
        [
            {"page": "a", "test": "1.1.1", "verdict": "conforme", "cas": "x"},
            {"page": "b", "test": "1.1.1", "verdict": "conforme", "cas": "x"},
        ],
        ["1.1"],
    )
    calcul = banc.agreger(incomplet, index)
    if calcul["taux"] is not None or "1.1" not in calcul["taux_motif"] or calcul["criteres"]:
        return _echec("un test sans relevé devrait retenir le taux")
    processus = ech(
        [
            {"page": "a", "test": "2.1.1", "verdict": "non_conforme", "cas": "x"},
            {"page": "b", "test": "2.1.1", "verdict": "conforme", "cas": "x"},
        ],
        ["2.1"],
        pages=[
            {"id": "a", "fichier": "a.html", "motifs": ["étape"], "processus": "contact"},
            {"id": "b", "fichier": "b.html", "motifs": ["étape"], "processus": "contact"},
        ],
    )
    calcul = banc.agreger(processus, index)
    if calcul["detail_pages"]["b"]["2.1"] != "non_conforme":
        return _echec("l'échec d'un processus devrait se propager à l'autre page")
    mixte = {
        "pages": [
            {"id": "a", "fichier": "a.html", "motifs": ["accueil"]},
            {"id": "b", "fichier": "b.html", "motifs": ["contact"]},
            {"id": "c", "fichier": "c.html", "motifs": ["article"]},
        ],
        "perimetre": ["2.1", "3.1"],
        "releves": [
            {"page": "a", "test": "2.1.1", "verdict": "conforme", "cas": "x"},
            {"page": "b", "test": "2.1.1", "verdict": "non_conforme", "cas": "x"},
            {"page": "c", "test": "2.1.1", "verdict": "non_conforme", "cas": "x"},
            {"page": "a", "test": "3.1.1", "verdict": "non_applicable", "cas": "y"},
            {"page": "b", "test": "3.1.1", "verdict": "non_applicable", "cas": "y"},
            {"page": "c", "test": "3.1.1", "verdict": "non_applicable", "cas": "y"},
        ],
    }
    calcul = banc.agreger(mixte, index)
    if calcul["taux"] != 0:
        return _echec("un critère non applicable ne devrait pas entrer dans le taux")
    print("Agrégation : ok.")
    return 0


def _echec(message: str) -> int:
    print(message)
    return 1


def main() -> int:
    if "--auto-test" in sys.argv:
        return auto_test()
    if "--ecrire" in sys.argv:
        ecrire()
        print("Échantillon recalculé.")
        return 0
    erreurs = banc.erreurs_echantillon(banc.CHEMIN_ECHANTILLON, banc.charger_index())
    if erreurs:
        print("\n".join(erreurs))
        return 1
    print("Échantillon cohérent avec ses relevés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
