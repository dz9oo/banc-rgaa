#!/usr/bin/env python3
"""Met à jour ou vérifie le tableau de couverture du README."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc


def main() -> int:
    tableau = banc.tableau_couverture()
    texte = banc.CHEMIN_README.read_text(encoding="utf-8")
    nouveau = banc.remplacer_couverture(texte, tableau)
    if "--verifier" in sys.argv:
        if nouveau != texte:
            print("Le tableau de couverture du README n'est pas à jour.")
            return 1
        print("Couverture à jour.")
        return 0
    banc.CHEMIN_README.write_text(nouveau, encoding="utf-8")
    print("README mis à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
