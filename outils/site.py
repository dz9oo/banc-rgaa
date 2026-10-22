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


STYLE = """
body { margin: 0; background: #fff; color: #1a1a1a; font-family: sans-serif; line-height: 1.5; }
main { max-width: 42rem; margin: 0 auto; padding: 0 1rem 3rem; }
nav, footer { max-width: 42rem; margin: 0 auto; padding: 1rem; }
a { color: #000091; }
a:focus { outline: 3px solid #000; outline-offset: 2px; }
code { font-family: ui-monospace, monospace; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; vertical-align: top; border-bottom: 1px solid #4d4d4d; padding: 0.3rem 0.5rem 0.3rem 0; }
"""


def page(titre: str, corps: str, profondeur: int) -> str:
    prefixe = "../" * profondeur
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{echapper(titre)}</title>
<style>{STYLE}</style>
</head>
<body>
<a href="#contenu">Aller au contenu</a>
<nav aria-label="Navigation du banc">
<p>
<a href="{prefixe}index.html">Accueil</a>
· <a href="{prefixe}cas/index.html">Cas</a>
· <a href="{prefixe}protocoles/index.html">Protocoles</a>
· <a href="{prefixe}echantillon.html">Échantillon</a>
</p>
</nav>
<main id="contenu">
{corps}
</main>
<footer>
<p>Banc d'essai communautaire pour le RGAA 4.1.2. Les verdicts revus sont des lectures contributives, reliées à la méthode officielle. Ce site ne signe pas une conformité.</p>
</footer>
</body>
</html>
"""


def ecrire(dest: Path, relatif: str, contenu: str) -> None:
    chemin = dest / relatif
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


def construire(dest: Path) -> None:
    if rapport("#000091", "#ffffff") < 4.5 or rapport("#1a1a1a", "#ffffff") < 4.5:
        raise RuntimeError("le thème du site n'atteint pas 4,5:1")
    index = banc.charger_index()
    cas = banc.charger_cas()
    compte = banc.compte_couverture(cas, index)
    echantillon = banc.lire_json(banc.CHEMIN_ECHANTILLON)
    connus = banc.tests_par_id(index)
    corps = [
        "<h1>Banc d'essai RGAA</h1>",
        "<p>Cas figés, protocoles et échantillon pour comparer un audit au RGAA 4.1.2. Un verdict s'accompagne de son motif et du lien vers le test officiel.</p>",
        "<h2>Couverture</h2>",
        "<table>",
        "<caption>Comptes du dépôt</caption>",
        "<thead><tr><th scope=\"col\">Indicateur</th><th scope=\"col\">Nombre</th></tr></thead>",
        "<tbody>",
        f"<tr><th scope=\"row\">Tests du référentiel</th><td>{compte['tests']}</td></tr>",
        f"<tr><th scope=\"row\">Protocoles rédigés</th><td>{compte['protocoles']}</td></tr>",
        f"<tr><th scope=\"row\">Cas revus</th><td>{compte['revus']}</td></tr>",
        f"<tr><th scope=\"row\">Cas non tranchés</th><td>{compte['non_tranches']}</td></tr>",
        "</tbody></table>",
    ]
    ecrire(dest, "index.html", page("Banc d'essai RGAA", "\n".join(corps), 0))
    groupes: dict[str, list] = {}
    for entree in cas:
        groupes.setdefault(entree["test"], []).append(entree)
    lignes = ["<h1>Cas</h1>", "<ul>"]
    for test in sorted(groupes, key=banc.cle_tri):
        intitule = connus[test]["intitule"]
        lignes.append(f"<li><a href=\"{test}/index.html\">{echapper(test)}</a> — {echapper(intitule)}</li>")
    lignes.append("</ul>")
    ecrire(dest, "cas/index.html", page("Cas", "\n".join(lignes), 1))
    for test, entrees in groupes.items():
        lignes = [f"<h1>Test {echapper(test)}</h1>", f"<p>{echapper(connus[test]['intitule'])}</p>", "<ul>"]
        for entree in sorted(entrees, key=lambda item: item["id"]):
            slug = entree["id"].split("/", 1)[1]
            lignes.append(
                f"<li><a href=\"{slug}.html\">{echapper(entree['titre'])}</a> — {LIBELLES[entree['verdict']]}, {LIBELLES[entree['statut']]}</li>"
            )
        lignes.append("</ul>")
        ecrire(dest, f"cas/{test}/index.html", page(f"Test {test}", "\n".join(lignes), 2))
        for entree in entrees:
            slug = entree["id"].split("/", 1)[1]
            source = f"../../../cas/rgaa-4.1.2/{test}/{slug}/page.html"
            blocs = [
                f"<h1>{echapper(entree['titre'])}</h1>",
                f"<p>Verdict : {LIBELLES[entree['verdict']]}. Nature : {LIBELLES[entree['nature']]}. Statut : {LIBELLES[entree['statut']]}.</p>",
                "<dl>",
                f"<dt>Test</dt><dd><a href=\"{echapper(entree['methode'])}\">{echapper(entree['test'])}</a></dd>",
                f"<dt>Modalités</dt><dd>{echapper(', '.join(entree['modalites']))}</dd>",
                "</dl>",
                "<h2>Motif</h2>",
                f"<p>{echapper(entree['motif'])}</p>",
            ]
            if entree.get("pieges"):
                blocs.append("<h2>Pièges</h2><ul>")
                blocs.extend(f"<li>{echapper(piege)}</li>" for piege in entree["pieges"])
                blocs.append("</ul>")
            if entree.get("desaccords"):
                blocs.append("<h2>Lectures</h2>")
                for lecture in entree["desaccords"]:
                    blocs.append(f"<h3>{echapper(lecture['lecture'])}</h3>")
                    blocs.append(f"<p>{echapper(lecture['motif'])}</p>")
            blocs.append(f"<p><a href=\"{source}\">Ouvrir la page du cas</a></p>")
            protocole = connus[test]["protocole"]
            if protocole:
                blocs.append(f"<p><a href=\"../../protocoles/{test}.html\">Protocole {echapper(test)}</a></p>")
            ecrire(
                dest,
                f"cas/{test}/{slug}.html",
                page(entree["titre"], "\n".join(blocs), 2),
            )
    lignes = ["<h1>Protocoles</h1>", "<ul>"]
    chemins = sorted(banc.CHEMIN_PROTOCOLES.glob("*.md"), key=lambda chemin: banc.cle_tri(chemin.stem))
    for chemin in chemins:
        meta, _corps = banc.decouper_protocole(chemin.read_text(encoding="utf-8"))
        lignes.append(
            f"<li><a href=\"{chemin.stem}.html\">{echapper(chemin.stem)}</a> — {LIBELLES[meta['nature']]}</li>"
        )
    lignes.append("</ul>")
    ecrire(dest, "protocoles/index.html", page("Protocoles", "\n".join(lignes), 1))
    for chemin in chemins:
        meta, corps = banc.decouper_protocole(chemin.read_text(encoding="utf-8"))
        blocs = [
            f"<h1>Protocole {echapper(meta['test'])}</h1>",
            f"<p>Nature : {LIBELLES[meta['nature']]}.</p>",
            f"<p><a href=\"{echapper(meta['methode'])}\">Test dans la méthode officielle</a></p>",
            "<h2>Ce qu'une machine peut établir</h2>",
            f"<p>{echapper(meta['machine'])}</p>",
            "<h2>Ce qu'une personne tranche</h2>",
            f"<p>{echapper(meta['personne'])}</p>",
            markdown_simple(corps),
        ]
        ecrire(dest, f"protocoles/{chemin.stem}.html", page(f"Protocole {meta['test']}", "\n".join(blocs), 1))
    lignes = [
        f"<h1>{echapper(echantillon['titre'])}</h1>",
        f"<p>{echapper(echantillon['taux_motif'])}</p>",
        "<h2>Pages</h2>",
        "<ul>",
    ]
    for page_ech in echantillon["pages"]:
        lignes.append(
            f"<li><a href=\"../echantillons/vitrine/{echapper(page_ech['fichier'])}\">{echapper(page_ech['id'])}</a> — {echapper(', '.join(page_ech['motifs']))}</li>"
        )
    lignes.append("</ul>")
    if echantillon["criteres"]:
        lignes.append("<h2>Critères couverts</h2><ul>")
        for critere in echantillon["criteres"]:
            lignes.append(
                f"<li>{echapper(critere['id'])} — {LIBELLES[critere['verdict']]}. {echapper(critere['motif'])}</li>"
            )
        lignes.append("</ul>")
    ecrire(dest, "echantillon.html", page(echantillon["titre"], "\n".join(lignes), 0))


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
    print("Site à jour.")
    return 0


def main() -> int:
    if "--verifier" in sys.argv:
        return verifier()
    if SITE.exists():
        shutil.rmtree(SITE)
    construire(SITE)
    print("Site écrit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
