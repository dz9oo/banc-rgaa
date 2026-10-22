#!/usr/bin/env python3
"""Produit ou vérifie l'index du RGAA 4.1.2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc


def main() -> int:
    verifier = "--verifier" in sys.argv
    if verifier:
        erreurs = banc.index_a_jour()
        if erreurs:
            print("\n".join(erreurs))
            return 1
        print(f"Index à jour : {banc.charger_index()['test_compte']} tests.")
        return 0
    index = banc.ecrire_index()
    print(f"Index écrit : {index['critere_compte']} critères, {index['test_compte']} tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
