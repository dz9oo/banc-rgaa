#!/usr/bin/env python3
"""Produit le site statique de lecture."""

import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc
import carte
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
            item("methode", f"{vers_site}methode.html", "Méthode"),
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
<p>{echapper(banc.phrase_fraicheur())}</p>
</footer>
</body>
</html>
"""


IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
LIBELLES_ENV = {"navigateur": "Navigateur", "viewport": "Viewport", "zoom": "Zoom"}


def lier_identifiants(html: str, connus: set[str]) -> str:
    def remplace(trouve: re.Match) -> str:
        identifiant = trouve.group(1)
        if identifiant not in connus:
            return trouve.group(0)
        test, slug = identifiant.split("/", 1)
        return f'<a href="../cas/{test}/{slug}.html"><code>{echapper(identifiant)}</code></a>'

    return re.sub(r"<code>(\d+\.\d+\.\d+/[a-z0-9-]+)</code>", remplace, html)


def json_fraicheur() -> str:
    info = banc.fraicheur()
    return (
        "{\n"
        f'  "date": "{info["date"]}",\n'
        f'  "commit": "{info["commit"]}",\n'
        f'  "texte": "{banc.phrase_fraicheur()}"\n'
        "}\n"
    )


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
    identifiants = {entree["id"] for entree in cas}
    ecrire(dest, "index.html", REDIRECTION)
    ecrire(dest, "methode.html", page("Les tests", carte.corps(index, cas), 0, "methode"))
    ecrire(dest, "donnees/fraicheur.json", json_fraicheur())
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
            ]
            if entree.get("relecture"):
                blocs.append(
                    f"<dt>Relecture</dt><dd>{echapper(vitrine.date_fr(entree['relecture']))}</dd>"
                )
            blocs.extend(
                [
                    "</dl>",
                    '<div class="feuille">',
                    "<h2>Motif</h2>",
                    f"<p>{echapper(entree['motif'])}</p>",
                    "</div>",
                ]
            )
            dossier = banc.CHEMIN_CAS / test / slug
            figures = []
            transcriptions = []
            for nom in entree["fichiers"]:
                if nom == "page.html":
                    continue
                href = f"../../../cas/rgaa-4.1.2/{test}/{slug}/{nom}"
                suffixe = Path(nom).suffix.lower()
                if suffixe in IMAGES:
                    figures.append(
                        "<figure>"
                        f'<img src="{echapper(href)}" alt="{echapper(entree["titre"])}">'
                        f"<figcaption>{echapper(nom)}</figcaption>"
                        "</figure>"
                    )
                elif suffixe == ".txt":
                    texte = (dossier / nom).read_text(encoding="utf-8") if (dossier / nom).is_file() else ""
                    note = ""
                    if "EXEMPLE" in texte:
                        note = (
                            " Cette transcription contient EXEMPLE. Aucune passe réelle n"
                            + APOS
                            + "est versée."
                        )
                    transcriptions.append(f'<p><a href="{echapper(href)}">{echapper(nom)}</a>.{note}</p>')
            if figures:
                blocs.append("<h2>Pièces visuelles</h2>")
                blocs.extend(figures)
            if transcriptions:
                blocs.append("<h2>Transcription</h2>")
                blocs.extend(transcriptions)
            if entree.get("cibles"):
                blocs.append("<h2>Cibles</h2><ul>")
                blocs.extend(
                    f'<li><code>{echapper(cible["selecteur"])}</code> {echapper(cible["note"])}</li>'
                    for cible in entree["cibles"]
                )
                blocs.append("</ul>")
            if entree.get("environnement"):
                blocs.append("<h2>Environnement</h2><dl>")
                for cle, valeur in entree["environnement"].items():
                    blocs.append(
                        f"<dt>{echapper(LIBELLES_ENV.get(cle, cle))}</dt><dd>{echapper(valeur)}</dd>"
                    )
                blocs.append("</dl>")
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
            autres = [item for item in entrees if item["id"] != entree["id"]]
            if autres:
                blocs.append("<h2>Autres cas de ce test</h2><ul>")
                for autre in autres:
                    autre_slug = autre["id"].split("/", 1)[1]
                    blocs.append(
                        "<li><a href=\""
                        + echapper(autre_slug)
                        + ".html\">"
                        + pilules_entree(autre, nature=False)
                        + " "
                        + echapper(autre["titre"])
                        + "</a></li>"
                    )
                blocs.append("</ul>")
            blocs.append("<h2>Page minimale</h2>")
            blocs.append(
                "<p class=\"texte\">Spécimen. La page jugée n" + APOS + "est pas modifiée.</p>"
            )
            blocs.append(
                f'<iframe class="specimen" title="Page minimale, {echapper(entree["titre"])}" src="{source}"></iframe>'
            )
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
            lier_identifiants(markdown_simple(corps_md), identifiants),
            "</div>",
            "<p>La nature du cas prime sur celle du protocole.</p>",
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
    revus_ids = {entree["id"] for entree in cas if entree["statut"] == "revu"}
    calcul = banc.agreger(echantillon, index, revus_ids)
    if calcul["taux"] is None:
        avertissement = (
            "Ces verdicts sont la grille d" + APOS + "un service fictif. "
            "Ce n" + APOS + "est pas une déclaration d" + APOS + "accessibilité. "
            "Un taux non publié n" + APOS + "est pas un zéro."
        )
    else:
        avertissement = (
            "Ces verdicts sont la grille d" + APOS + "un service fictif. "
            "Ce n" + APOS + "est pas une déclaration d" + APOS + "accessibilité."
        )
    lignes = [
        '<p class="surtitre">Vitrine</p>',
        f"<h1>{echapper(echantillon['titre'])}</h1>",
        f'<p class="limite">{echapper(calcul["taux_motif"])}</p>',
        f'<p class="texte">{avertissement}</p>',
        "<h2>Pages</h2>",
        f'<ul class="catalogue compact">{"".join(cartes)}</ul>',
    ]
    if calcul["criteres"]:
        fiches = []
        for critere in calcul["criteres"]:
            fiches.append(
                "<li>"
                + f'<span class="ligne-pilules">{span_pilule(LIBELLES[critere["verdict"]])}</span>'
                + f"<strong>{echapper(critere['id'])}</strong>"
                + f'<span class="intitule">{echapper(critere["motif"])}</span>'
                + "</li>"
            )
        lignes.append("<h2>Critères couverts</h2>")
        lignes.append(f'<ul class="pile">{"".join(fiches)}</ul>')
    if calcul["manques"]:
        lignes.append("<h2>Critères ouverts</h2>")
        lignes.append(
            "<p class=\"texte\">Un critère ouvert n"
            + APOS
            + "a pas, sur chaque page, un relevé qui cite un cas revu.</p>"
        )
        ouverts = []
        for critere, tests_manquants in sorted(calcul["manques"].items(), key=lambda item: banc.cle_tri(item[0])):
            liens_tests = []
            for test_id in tests_manquants:
                lien = f'<a href="{echapper(connus[test_id]["methode"])}">{echapper(test_id)}</a>'
                if test_id in groupes:
                    lien += f' <a href="cas/{echapper(test_id)}/index.html">cas</a>'
                liens_tests.append(lien)
            ouverts.append(
                "<li>"
                + span_pilule("Ouvert", "ouvert")
                + f"<strong>{echapper(critere)}</strong>"
                + f'<span class="intitule">{" · ".join(liens_tests)}</span>'
                + "</li>"
            )
        lignes.append(f'<ul class="pile">{"".join(ouverts)}</ul>')
    ecrire(dest, "echantillon.html", page(echantillon["titre"], "\n".join(lignes), 0, "echantillon"))


def verifier_fiches(dest: Path) -> None:
    vision = (dest / "cas/3.2.1/texte-en-image.html").read_text(encoding="utf-8")
    if "capture.png" not in vision or "Chromium" not in vision or "<iframe" not in vision:
        raise RuntimeError("la fiche texte-en-image n'affiche pas la capture, l'environnement et la page")
    geste = (dest / "cas/10.7.1/focus-absent.html").read_text(encoding="utf-8")
    if "<code>a</code>" not in geste or "capture.png" not in geste:
        raise RuntimeError("la fiche focus-absent n'affiche pas la cible ni la capture")
    audio = (dest / "cas/4.13.1/lecteur-audio.html").read_text(encoding="utf-8")
    if "transcription.txt" not in audio or "EXEMPLE" not in audio:
        raise RuntimeError("la fiche audio ne signale pas la transcription d'exemple")
    protocole = (dest / "protocoles/6.1.1.html").read_text(encoding="utf-8")
    if "../cas/6.1.1/cliquez-ici.html" not in protocole or "La nature du cas prime" not in protocole:
        raise RuntimeError("le protocole 6.1.1 ne lie pas ses cas")
    page_echantillon = (dest / "echantillon.html").read_text(encoding="utf-8")
    for critere in ("1.2", "1.3", "3.2", "6.1", "8.1"):
        if f"<strong>{critere}</strong>" not in page_echantillon:
            raise RuntimeError(f"le critère ouvert {critere} manque sur l'échantillon")
    if "Ouvert" not in page_echantillon or "pas un zéro" not in page_echantillon:
        raise RuntimeError("l'échantillon ne distingue pas un taux vide d'un zéro")


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
            gauche_texte = (dest / relatif).read_text(encoding="utf-8")
            droite_texte = (SITE / relatif).read_text(encoding="utf-8")
            if banc.normaliser_fraicheur(gauche_texte) != banc.normaliser_fraicheur(droite_texte):
                print(f"Contenu différent : {relatif}")
                return 1
        carte.verifier((dest / "methode.html").read_text(encoding="utf-8"), banc.charger_index(), banc.charger_cas())
        verifier_fiches(dest)
    accueil = banc.RACINE / "index.html"
    html = vitrine.rendre()
    if not accueil.is_file() or banc.normaliser_fraicheur(accueil.read_text(encoding="utf-8")) != banc.normaliser_fraicheur(html):
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
