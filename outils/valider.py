#!/usr/bin/env python3
"""Valide le corpus et rejoue des cas qui doivent échouer."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc


def auto_test() -> list[str]:
    erreurs = []
    index = banc.construire_index()
    with tempfile.TemporaryDirectory() as dossier:
        racine = Path(dossier)
        mauvais = racine / "8.5.1" / "titre-faux"
        mauvais.mkdir(parents=True)
        (mauvais / "page.html").write_text("<!DOCTYPE html><html lang=\"fr\"><title>A</title></html>\n", encoding="utf-8")
        banc.ecrire_json(
            mauvais / "cas.json",
            {
                "id": "8.5.1/titre-faux",
                "referentiel": "RGAA",
                "version": "4.1.2",
                "test": "8.5.1",
                "titre": "Méthode vers un autre test",
                "verdict": "conforme",
                "nature": "deterministe",
                "modalites": ["html"],
                "motif": "x" * 80,
                "methode": banc.methode_du_test("8.3.1"),
                "statut": "brouillon",
                "fichiers": ["page.html"],
                "licence": "etalab-2.0",
                "origine": "original",
            },
        )
        messages = banc.erreurs_cas(mauvais, index)
        if not any("methode" in message for message in messages):
            erreurs.append("un cas dont la méthode vise un autre test aurait dû échouer")
        flou = racine / "6.1.1" / "sans-lectures"
        flou.mkdir(parents=True)
        (flou / "page.html").write_text("<!DOCTYPE html><html lang=\"fr\"><title>A</title></html>\n", encoding="utf-8")
        banc.ecrire_json(
            flou / "cas.json",
            {
                "id": "6.1.1/sans-lectures",
                "referentiel": "RGAA",
                "version": "4.1.2",
                "test": "6.1.1",
                "titre": "Deux lectures absentes",
                "verdict": "non_tranche",
                "nature": "pertinence",
                "modalites": ["html"],
                "motif": "y" * 80,
                "methode": banc.methode_du_test("6.1.1"),
                "statut": "brouillon",
                "fichiers": ["page.html"],
                "licence": "etalab-2.0",
                "origine": "original",
                "desaccords": [],
            },
        )
        messages = banc.erreurs_cas(flou, index)
        if not any("desaccords" in message for message in messages):
            erreurs.append("un non tranché sans deux lectures aurait dû échouer")
    if not erreurs:
        print("Contrôles négatifs : ok.")
    return erreurs


def main() -> int:
    erreurs = banc.index_a_jour()
    if erreurs:
        print("\n".join(erreurs))
        return 1
    index = banc.charger_index()
    cas = []
    for dossier in banc.dossiers_cas():
        erreurs.extend(banc.erreurs_cas(dossier, index))
        if (dossier / "cas.json").is_file():
            try:
                entree = banc.lire_json(dossier / "cas.json")
                entree["test"] = entree.get("test")
                cas.append(entree)
            except json.JSONDecodeError:
                pass
    if banc.CHEMIN_PROTOCOLES.is_dir():
        for chemin in sorted(banc.CHEMIN_PROTOCOLES.glob("*.md")):
            erreurs.extend(banc.erreurs_protocole(chemin, index, cas))
    if not banc.CHEMIN_ECHANTILLON.is_file():
        erreurs.append("échantillon vitrine absent")
    else:
        erreurs.extend(banc.erreurs_echantillon(banc.CHEMIN_ECHANTILLON, index))
    erreurs.extend(auto_test())
    if erreurs:
        print("\n".join(erreurs))
        return 1
    print(f"Corpus valide : {len(cas)} cas, {index['test_compte']} tests dans l'index.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
