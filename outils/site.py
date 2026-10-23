#!/usr/bin/env python3
"""Produit le site statique de lecture."""

import filecmp
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc
import vitrine

SITE = banc.RACINE / "site"
LIBELLES = {
    "conforme": "Conforme",
    "non_conforme": "Non conforme",
    "non_applicable": "Non applicable",
    "non_tranche": "Non tranché",
    "deterministe": "Déterministe",
    "pertinence": "Pertinence",
    "vision": "Vision",
    "restitution": "Restitution",
    "geste": "Geste",
    "document": "Document",
    "brouillon": "Brouillon",
    "revu": "Revu",
}


def luminance(hexadecimal: str) -> float:
    def canal(valeur: int) -> float:
        srgb = valeur / 255
        if srgb <= 0.04045:
            return srgb / 12.92
        return ((srgb + 0.055) / 1.055) ** 2.4

    nombre = hexadecimal.removeprefix("#")
    rouge, vert, bleu = int(nombre[0:2], 16), int(nombre[2:4], 16), int(nombre[4:6], 16)
    return 0.2126 * canal(rouge) + 0.7152 * canal(vert) + 0.0722 * canal(bleu)


def rapport(avant: str, arriere: str) -> float:
    premier, second = luminance(avant), luminance(arriere)
    clair, sombre = max(premier, second), min(premier, second)
    return (clair + 0.05) / (sombre + 0.05)


def echapper(texte: str) -> str:
    return (
        str(texte)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def inline(texte: str) -> str:
    morceaux = re.split(r"(`[^`]+`)", texte)
    html = []
    for morceau in morceaux:
        if morceau.startswith("`") and morceau.endswith("`") and len(morceau) >= 2:
            html.append("<code>" + echapper(morceau[1:-1]) + "</code>")
        else:
            html.append(echapper(morceau))
    return "".join(html)


def markdown_simple(texte: str) -> str:
    lignes = texte.replace("\r\n", "\n").split("\n")
    html: list[str] = []
    paragraphe: list[str] = []
    items: list[str] = []

    def verser_paragraphe() -> None:
        if paragraphe:
            html.append("<p>" + inline(" ".join(paragraphe)) + "</p>")
            paragraphe.clear()

    def verser_items() -> None:
        if items:
            html.append("<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>")
            items.clear()

    for ligne in lignes:
        if ligne.startswith("## "):
            verser_paragraphe()
            verser_items()
            html.append(f"<h2>{inline(ligne[3:])}</h2>")
        elif ligne.startswith("- "):
            verser_paragraphe()
            items.append(ligne[2:])
        elif not ligne.strip():
            verser_paragraphe()
            verser_items()
        else:
            verser_items()
            paragraphe.append(ligne.strip())
    verser_paragraphe()
    verser_items()
    return "\n".join(html)


APOS = "\u2019"
MARQUE = f"Banc d{APOS}essai RGAA"

PAIRES = (
    ("#1a1916", "#f6f5f2"),
    ("#1a1916", "#ffffff"),
    ("#1a1916", "#e7efe9"),
    ("#1a1916", "#f4ead6"),
    ("#1a1916", "#e7e6f2"),
    ("#1a1916", "#eeeae4"),
    ("#1d4a38", "#f6f5f2"),
    ("#1d4a38", "#ffffff"),
    ("#1d4a38", "#e5efe8"),
    ("#1d4a38", "#f3eadc"),
    ("#3f3b36", "#f6f5f2"),
    ("#3f3b36", "#ffffff"),
    ("#f6f5f2", "#1a1916"),
)

REDIRECTION = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="0; url=../index.html">
<title>{MARQUE}</title>
<link rel="stylesheet" href="../habillage.css">
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<main id="contenu">
<p class="limite"><a href="../index.html">Aller à la page d{APOS}accueil du banc d{APOS}essai.</a></p>
</main>
</body>
</html>
"""


def etiquette(nombre: int, singulier: str, pluriel: str) -> str:
    if nombre == 1:
        return f"1 {singulier}"
    return f"{nombre} {pluriel}"


def span_pilule(libelle: str, classe: str = "") -> str:
    suffixe = f" {classe}" if classe else ""
    return f'<span class="pilule{suffixe}">{echapper(libelle)}</span>'


def pilules_entree(entree: dict, nature: bool) -> str:
    if entree["statut"] == "brouillon":
        classe_statut = "brouillon"
    elif entree["verdict"] == "non_tranche":
        classe_statut = "ouvert"
    else:
        classe_statut = ""
    morceaux = [span_pilule(LIBELLES[entree["statut"]], classe_statut)]
    if entree["statut"] == "brouillon":
        morceaux.append(
            '<span class="propose">Verdict proposé, '
            + echapper(LIBELLES[entree["verdict"]].lower())
            + "</span>"
        )
    else:
        classe_verdict = "ouvert" if entree["verdict"] == "non_tranche" else ""
        morceaux.append(span_pilule(LIBELLES[entree["verdict"]], classe_verdict))
    if nature:
        morceaux.append(span_pilule(LIBELLES[entree["nature"]]))
    return " ".join(morceaux)


def pilules_groupe(entrees: list) -> str:
    revus = sum(1 for entree in entrees if entree["statut"] == "revu")
    brouillons = sum(1 for entree in entrees if entree["statut"] == "brouillon")
    ouverts = sum(
        1
        for entree in entrees
        if entree["statut"] == "revu" and entree["verdict"] == "non_tranche"
    )
    morceaux = []
    if revus:
        morceaux.append(span_pilule(etiquette(revus, "revu", "revus")))
    if ouverts:
        morceaux.append(span_pilule(etiquette(ouverts, "non tranché", "non tranchés"), "ouvert"))
    if brouillons:
        morceaux.append(span_pilule(etiquette(brouillons, "brouillon", "brouillons"), "brouillon"))
    return "".join(morceaux)


def par_theme(index: dict, retenir) -> list[dict]:
    ordre: list[int] = []
    paquets: dict[int, dict] = {}
    for test in index["tests"]:
        if not retenir(test):
            continue
        cle = test["thematique"]
        if cle not in paquets:
            ordre.append(cle)
            paquets[cle] = {"titre": test["thematique_titre"], "tests": []}
        paquets[cle]["tests"].append(test)
    return [paquets[cle] for cle in ordre]


def page(titre: str, corps: str, profondeur: int, courant: str) -> str:
    vers_site = "../" * profondeur
    vers_racine = "../" * (profondeur + 1)

    def item(cle: str, href: str, libelle: str) -> str:
        ici = ' aria-current="page"' if cle == courant else ""
        return f'<a href="{href}"{ici}>{libelle}</a>'

    navigation = "\n".join(
        [
            item("", f"{vers_racine}index.html", "Accueil"),
            item("cas", f"{vers_site}cas/index.html", "Cas"),
            item("protocoles", f"{vers_site}protocoles/index.html", "Protocoles"),
            item("echantillon", f"{vers_site}echantillon.html", "Échantillon"),
        ]
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{echapper(titre)} — {MARQUE}</title>
<link rel="stylesheet" href="{vers_racine}habillage.css">
</head>
<body>
<a class="evitement" href="#contenu">Aller au contenu</a>
<header class="barre">
<a class="marque" href="{vers_racine}index.html">Banc d{APOS}essai</a>
<nav class="site-nav" aria-label="Navigation du banc">
{navigation}
</nav>
</header>
<main id="contenu">
{corps}
</main>
<footer class="pied">
<p>Les verdicts revus sont des lectures contributives. Les cas sont sous Licence Ouverte 2.0.</p>
</footer>
</body>
</html>
"""


def ecrire(dest: Path, relatif: str, contenu: str) -> None:
    chemin = dest / relatif
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


def phrase_catalogue(revus: int, brouillons: int) -> str:
    morceaux = []
    if revus:
        morceaux.append(etiquette(revus, "cas revu", "cas revus"))
    if brouillons:
        morceaux.append(etiquette(brouillons, "brouillon", "brouillons"))
    if not morceaux:
        tete = "Aucun cas pour l" + APOS + "instant."
    elif len(morceaux) == 1:
        tete = morceaux[0] + "."
    else:
        tete = f"{morceaux[0]}, {morceaux[1]}."
    return (
        tete
        + " Le statut se lit avant le verdict. Un brouillon ne se cite pas. "
        + "Les tests sans cas ne figurent pas ici."
    )


def construire(dest: Path) -> None:
    for avant, arriere in PAIRES:
        if rapport(avant, arriere) < 4.5:
            raise RuntimeError(f"contraste insuffisant {avant} sur {arriere}")
    if not (banc.RACINE / "habillage.css").is_file():
        raise RuntimeError("habillage.css absent")
    index = banc.charger_index()
    cas = banc.charger_cas()
    echantillon = banc.lire_json(banc.CHEMIN_ECHANTILLON)
    connus = banc.tests_par_id(index)
    ecrire(dest, "index.html", REDIRECTION)
    groupes: dict[str, list] = {}
    for entree in cas:
        groupes.setdefault(entree["test"], []).append(entree)
    sections = []
    for theme in par_theme(index, lambda test: test["id"] in groupes):
        cartes = []
        for test in theme["tests"]:
            cartes.append(
                "<li><a href=\""
                + echapper(test["id"])
                + "/index.html\">"
                + f'<span class="numero">{echapper(test["id"])}</span>'
                + f'<span class="intitule">{echapper(test["intitule"])}</span>'
                + f'<span class="ligne-pilules">{pilules_groupe(groupes[test["id"]])}</span>'
                + "</a></li>"
            )
        sections.append(
            f"<section><h2>{echapper(theme['titre'])}</h2>"
            f"<ul class=\"catalogue\">{''.join(cartes)}</ul></section>"
        )
    revus = sum(1 for entree in cas if entree["statut"] == "revu")
    brouillons = sum(1 for entree in cas if entree["statut"] == "brouillon")
    corps = "\n".join(
        [
            '<p class="surtitre">Catalogue</p>',
            "<h1>Les cas</h1>",
            f'<p class="limite">{echapper(phrase_catalogue(revus, brouillons))}</p>',
            *sections,
        ]
    )
    ecrire(dest, "cas/index.html", page("Les cas", corps, 1, "cas"))
    for test, entrees in groupes.items():
        fiches = []
        for entree in sorted(entrees, key=lambda item: item["id"]):
            slug = entree["id"].split("/", 1)[1]
            fiches.append(
                "<li><a href=\""
                + echapper(slug)
                + ".html\">"
                + f'<span class="ligne-pilules">{pilules_entree(entree, nature=False)}</span>'
                + f"<strong>{echapper(entree['titre'])}</strong>"
                + "</a></li>"
            )
        liens = [
            f'<a href="{echapper(connus[test]["methode"])}">Test officiel {echapper(test)}</a>'
        ]
        if connus[test]["protocole"]:
            liens.append(f'<a href="../../protocoles/{echapper(test)}.html">Protocole</a>')
        corps = "\n".join(
            [
                '<a class="retour" href="../index.html">Retour aux cas</a>',
                '<p class="surtitre">Test</p>',
                f"<h1>{echapper(test)}</h1>",
                f'<p class="limite">{echapper(connus[test]["intitule"])}</p>',
                f'<p class="texte">{" · ".join(liens)}</p>',
                f'<ul class="pile">{"".join(fiches)}</ul>',
            ]
        )
        ecrire(dest, f"cas/{test}/index.html", page(f"Test {test}", corps, 2, "cas"))
        for entree in entrees:
            slug = entree["id"].split("/", 1)[1]
            source = f"../../../cas/rgaa-4.1.2/{test}/{slug}/page.html"
            blocs = [
                f'<a class="retour" href="index.html">Retour au test {echapper(test)}</a>',
                f'<p class="surtitre">{echapper(test)}</p>',
                f"<h1>{echapper(entree['titre'])}</h1>",
                f'<p class="ligne-pilules">{pilules_entree(entree, nature=True)}</p>',
                "<dl>",
                f'<dt>Test</dt><dd><a href="{echapper(entree["methode"])}">{echapper(entree["test"])}</a></dd>',
                f"<dt>Modalités</dt><dd>{echapper(', '.join(entree['modalites']))}</dd>",
                "</dl>",
                '<div class="feuille">',
                "<h2>Motif</h2>",
                f"<p>{echapper(entree['motif'])}</p>",
                "</div>",
            ]
            if entree.get("pieges"):
                blocs.append("<h2>Pièges</h2><ul>")
                blocs.extend(f"<li>{echapper(piege)}</li>" for piege in entree["pieges"])
                blocs.append("</ul>")
            if entree.get("desaccords"):
                cartes = []
                for lecture in entree["desaccords"]:
                    cartes.append(
                        "<div><h3>"
                        + echapper(lecture["lecture"])
                        + "</h3><p>"
                        + echapper(lecture["motif"])
                        + "</p></div>"
                    )
                blocs.append('<h2>Lectures</h2><div class="lectures">' + "".join(cartes) + "</div>")
            actions = [f'<a class="action" href="{source}">Ouvrir la page minimale</a>']
            if connus[test]["protocole"]:
                actions.append(
                    f'<a class="action" href="../../protocoles/{echapper(test)}.html">Protocole {echapper(test)}</a>'
                )
            blocs.append('<p class="actions">' + "".join(actions) + "</p>")
            ecrire(
                dest,
                f"cas/{test}/{slug}.html",
                page(entree["titre"], "\n".join(blocs), 2, "cas"),
            )
    chemins = sorted(banc.CHEMIN_PROTOCOLES.glob("*.md"), key=lambda chemin: banc.cle_tri(chemin.stem))
    metas = {
        chemin.stem: banc.decouper_protocole(chemin.read_text(encoding="utf-8"))[0]
        for chemin in chemins
    }
    sections = []
    for theme in par_theme(index, lambda test: test["id"] in metas):
        cartes = []
        for test in theme["tests"]:
            meta = metas[test["id"]]
            cartes.append(
                "<li><a href=\""
                + echapper(test["id"])
                + ".html\">"
                + f'<span class="numero">{echapper(test["id"])}</span>'
                + f'<span class="intitule">{echapper(test["intitule"])}</span>'
                + f'<span class="ligne-pilules">{span_pilule(LIBELLES[meta["nature"]])}</span>'
                + "</a></li>"
            )
        sections.append(
            f"<section><h2>{echapper(theme['titre'])}</h2>"
            f"<ul class=\"catalogue\">{''.join(cartes)}</ul></section>"
        )
    corps = "\n".join(
        [
            '<p class="surtitre">Méthode</p>',
            "<h1>Protocoles</h1>",
            "<p class=\"limite\">Un protocole dit ce qu" + APOS + "une machine peut établir, et ce qu"
            + APOS + "une personne tranche. La nature du cas prime sur celle du protocole.</p>",
            *sections,
        ]
    )
    ecrire(dest, "protocoles/index.html", page("Protocoles", corps, 1, "protocoles"))
    for chemin in chemins:
        meta, corps_md = banc.decouper_protocole(chemin.read_text(encoding="utf-8"))
        blocs = [
            '<a class="retour" href="index.html">Retour aux protocoles</a>',
            '<p class="surtitre">Protocole</p>',
            f"<h1>{echapper(meta['test'])}</h1>",
            f'<p class="ligne-pilules">{span_pilule(LIBELLES[meta["nature"]])}</p>',
            f'<p class="limite">{echapper(connus[meta["test"]]["intitule"])}</p>',
            f'<p><a href="{echapper(meta["methode"])}">Test officiel {echapper(meta["test"])}</a></p>',
            '<div class="lectures">',
            "<div><h2>Ce qu" + APOS + "une machine peut établir</h2>"
            + f"<p>{echapper(meta['machine'])}</p></div>",
            "<div><h2>Ce qu" + APOS + "une personne tranche</h2>"
            + f"<p>{echapper(meta['personne'])}</p></div>",
            "</div>",
            '<div class="prose">',
            markdown_simple(corps_md),
            "</div>",
        ]
        ecrire(
            dest,
            f"protocoles/{chemin.stem}.html",
            page(f"Protocole {meta['test']}", "\n".join(blocs), 1, "protocoles"),
        )
    cartes = []
    for page_ech in echantillon["pages"]:
        cartes.append(
            '<li><a href="../echantillons/vitrine/'
            + echapper(page_ech["fichier"])
            + '">'
            + f'<span class="numero">{echapper(page_ech["id"])}</span>'
            + f'<span class="intitule">{echapper(", ".join(page_ech["motifs"]))}</span>'
            + "</a></li>"
        )
    lignes = [
        '<p class="surtitre">Vitrine</p>',
        f"<h1>{echapper(echantillon['titre'])}</h1>",
        f'<p class="limite">{echapper(echantillon["taux_motif"])}</p>',
        "<h2>Pages</h2>",
        f'<ul class="catalogue compact">{"".join(cartes)}</ul>',
    ]
    if echantillon["criteres"]:
        fiches = []
        for critere in echantillon["criteres"]:
            fiches.append(
                "<li>"
                + f'<span class="ligne-pilules">{span_pilule(LIBELLES[critere["verdict"]])}</span>'
                + f"<strong>{echapper(critere['id'])}</strong>"
                + f'<span class="intitule">{echapper(critere["motif"])}</span>'
                + "</li>"
            )
        lignes.append("<h2>Critères couverts</h2>")
        lignes.append(f'<ul class="pile">{"".join(fiches)}</ul>')
    ecrire(dest, "echantillon.html", page(echantillon["titre"], "\n".join(lignes), 0, "echantillon"))


def verifier() -> int:
    with tempfile.TemporaryDirectory() as dossier:
        dest = Path(dossier) / "site"
        construire(dest)
        if not SITE.is_dir():
            print("site/ absent")
            return 1
        gauche = sorted(chemin.relative_to(dest).as_posix() for chemin in dest.rglob("*") if chemin.is_file())
        droite = sorted(chemin.relative_to(SITE).as_posix() for chemin in SITE.rglob("*") if chemin.is_file())
        if gauche != droite:
            print("Le site commité ne contient pas les mêmes fichiers qu'une régénération.")
            print("Régénéré :", ", ".join(gauche))
            print("Commité :", ", ".join(droite))
            return 1
        for relatif in gauche:
            if not filecmp.cmp(dest / relatif, SITE / relatif, shallow=False):
                print(f"Contenu différent : {relatif}")
                return 1
    accueil = banc.RACINE / "index.html"
    html = vitrine.rendre()
    if not accueil.is_file() or accueil.read_text(encoding="utf-8") != html:
        print("index.html n'est pas à jour. Relancer : python3 outils/site.py")
        return 1
    print("Site à jour.")
    return 0


def main() -> int:
    if "--verifier" in sys.argv:
        return verifier()
    if SITE.exists():
        shutil.rmtree(SITE)
    construire(SITE)
    (banc.RACINE / "index.html").write_text(vitrine.rendre(), encoding="utf-8")
    print("Site écrit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
