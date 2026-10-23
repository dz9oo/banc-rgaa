#!/usr/bin/env python3
"""Carte des 258 tests : relu, brouillon seulement, ou vide."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc

APOS = "\u2019"

ETAT_REVU = "Au moins un cas revu"
ETAT_BROUILLON = "Brouillon seulement"
ETAT_VIDE = "Pas de cas"


def echapper(texte: str) -> str:
    return (
        str(texte)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def etats(cas: list[dict]) -> dict[str, str]:
    par_test: dict[str, list[dict]] = {}
    for entree in cas:
        par_test.setdefault(entree["test"], []).append(entree)
    resultat = {}
    for test, entrees in par_test.items():
        if any(entree["statut"] == "revu" for entree in entrees):
            resultat[test] = "revu"
        elif entrees:
            resultat[test] = "brouillon"
    return resultat


def _groupes(index: dict) -> list[dict]:
    themes: list[dict] = []
    courant_theme = None
    courant_critere = None
    for test in index["tests"]:
        if courant_theme is None or courant_theme["id"] != test["thematique"]:
            courant_theme = {
                "id": test["thematique"],
                "titre": test["thematique_titre"],
                "criteres": [],
            }
            themes.append(courant_theme)
            courant_critere = None
        if courant_critere is None or courant_critere["id"] != test["critere"]:
            courant_critere = {
                "id": test["critere"],
                "intitule": test["critere_intitule"],
                "tests": [],
            }
            courant_theme["criteres"].append(courant_critere)
        courant_critere["tests"].append(test)
    return themes


def corps(index: dict, cas: list[dict]) -> str:
    classement = etats(cas)
    comptes = {"revu": 0, "brouillon": 0, "vide": 0}
    for test in index["tests"]:
        comptes[classement.get(test["id"], "vide")] += 1
    revus = sum(1 for entree in cas if entree["statut"] == "revu")
    brouillons = sum(1 for entree in cas if entree["statut"] == "brouillon")
    lignes = [
        '<p class="surtitre">Méthode</p>',
        "<h1>Les 258 tests</h1>",
        "<p class=\"limite\">Chaque test est relu, seulement en brouillon, ou vide. "
        "Ce n" + APOS + "est pas un taux, ni une déclaration.</p>",
        "<p class=\"texte\">"
        f"{index['test_compte']} tests, {index['critere_compte']} critères. "
        f"{comptes['revu']} ont au moins un cas revu. "
        f"{comptes['brouillon']} sont seulement en brouillon. "
        f"{comptes['vide']} n" + APOS + "ont pas de cas. "
        f"{revus} cas revus et {brouillons} brouillons, comptés comme des cas."
        "</p>",
        "<p class=\"texte\">Le RGAA 5 n" + APOS + "est pas importé : la méthode est encore en rédaction.</p>",
        '<form class="recherche" role="search" id="forme-carte" action="methode.html" method="get">',
        '<label for="numero">Numéro ou mot de l' + APOS + "intitulé</label>",
        '<input id="numero" name="numero" type="search" placeholder="6.1.1 ou doctype" autocomplete="off" spellcheck="false">',
        '<button type="submit">Filtrer</button>',
        "</form>",
        '<p class="annonce">Sans script, les tests restent tous visibles. Avec script, le champ filtre cette page.</p>',
        '<p id="aucun-carte" hidden>Aucun test pour <span id="aucun-carte-numero"></span>.</p>',
    ]
    for theme in _groupes(index):
        blocs = [f'<section data-theme="{theme["id"]}"><h2>{echapper(theme["titre"])}</h2>']
        for critere in theme["criteres"]:
            blocs.append(
                f'<section data-critere="{echapper(critere["id"])}">'
                f'<h3>{echapper(critere["id"])}</h3>'
                f'<p class="limite">{echapper(critere["intitule"])}</p>'
            )
            for test in critere["tests"]:
                etat = classement.get(test["id"], "vide")
                if etat == "revu":
                    suite = (
                        f"{ETAT_REVU}. "
                        f'<a href="cas/{echapper(test["id"])}/index.html">Les cas</a>'
                    )
                elif etat == "brouillon":
                    suite = (
                        f"{ETAT_BROUILLON}. Le verdict ne se cite pas. "
                        f'<a href="cas/{echapper(test["id"])}/index.html">Les cas</a>'
                    )
                else:
                    titre = "Cas : " + test["id"]
                    lien = (
                        "https://github.com/dz9oo/banc-rgaa/issues/new?template=cas.yml"
                        f"&title={titre.replace(' ', '%20').replace(':', '%3A')}"
                        f"&test={test['id']}"
                    )
                    suite = (
                        f"{ETAT_VIDE}. "
                        f'<a href="{echapper(lien)}">Proposer un cas</a>'
                    )
                blocs.append(
                    f'<article data-test="{echapper(test["id"])}" '
                    f'data-intitule="{echapper(test["intitule"])}">'
                    f'<h4><a href="{echapper(test["methode"])}">{echapper(test["id"])}</a></h4>'
                    f'<p>{echapper(test["intitule"])}</p>'
                    f"<p>{suite}</p>"
                    "</article>"
                )
            blocs.append("</section>")
        blocs.append("</section>")
        lignes.extend(blocs)
    lignes.append('<script src="../outils/carte-filtre.js"></script>')
    lignes.append(
        """<script>
(function () {
  var racine = document.getElementById("contenu");
  var champ = document.getElementById("numero");
  var aucun = document.getElementById("aucun-carte");
  var numero = document.getElementById("aucun-carte-numero");
  var forme = document.getElementById("forme-carte");
  var params = new URLSearchParams(window.location.search);
  if (params.get("numero")) champ.value = params.get("numero");
  function filtrer() {
    var q = champ.value;
    var n = window.CarteFiltre.appliquer(racine, q);
    aucun.hidden = q.trim() === "" || n !== 0;
    numero.textContent = q.trim();
    var url = new URL(window.location.href);
    if (q.trim()) url.searchParams.set("numero", q.trim());
    else url.searchParams.delete("numero");
    try { window.history.replaceState(null, "", url); } catch (e) {}
  }
  forme.addEventListener("submit", function (event) {
    event.preventDefault();
    filtrer();
  });
  champ.addEventListener("input", filtrer);
  filtrer();
})();
</script>"""
    )
    return "\n".join(lignes)


def verifier(html: str, index: dict, cas: list[dict]) -> None:
    ids = re.findall(r'data-test="([^"]+)"', html)
    attendus = [test["id"] for test in index["tests"]]
    if ids != attendus:
        raise RuntimeError("la carte ne liste pas chaque test une fois, dans l'ordre du référentiel")
    classement = etats(cas)
    comptes = {"revu": 0, "brouillon": 0, "vide": 0}
    for test in attendus:
        comptes[classement.get(test, "vide")] += 1
    if sum(comptes.values()) != index["test_compte"]:
        raise RuntimeError("les trois états ne partitionnent pas les tests")
    articles = dict(re.findall(r'<article data-test="([^"]+)"[^>]*>(.*?)</article>', html, re.S))
    if "Pas de cas" not in articles.get("1.1.1", "") or "Les cas" in articles.get("1.1.1", ""):
        raise RuntimeError("1.1.1 devrait être vide, sans verdict")
    if ETAT_REVU not in articles.get("8.1.1", "") or "cas/8.1.1/index.html" not in articles.get("8.1.1", ""):
        raise RuntimeError("8.1.1 devrait mener aux cas revus")
    brouillon = articles.get("4.13.1", "")
    if ETAT_BROUILLON not in brouillon or "ne se cite pas" not in brouillon:
        raise RuntimeError("4.13.1 devrait être un brouillon non citable")
    if "Conforme" in brouillon or "Non conforme" in brouillon:
        raise RuntimeError("4.13.1 ne doit pas afficher son verdict")
    if "RGAA 5" not in html:
        raise RuntimeError("la carte doit dire que le RGAA 5 n'est pas importé")
    if re.search(r"\d+\s*/\s*\d+", html):
        raise RuntimeError("la carte ne publie pas un ratio de couverture")
