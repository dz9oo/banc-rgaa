#!/usr/bin/env python3
"""Produit la page vitrine (index.html) à partir du modèle et des cas."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banc

MODELE = Path(__file__).resolve().parent / "vitrine.modele.html"
APOS = "\u2019"
NBSP = "\u00a0"
NNBSP = "\u202f"

LIBELLES = {
    "conforme": "Conforme",
    "non_conforme": "Non conforme",
    "non_applicable": "Non applicable",
    "non_tranche": "Non tranché",
    "brouillon": "Brouillon",
    "revu": "Revu",
}

POLICES = (
    "NotoSerifDisplay-Medium.woff2",
    "NotoSans-Regular.woff2",
    "NotoSans-Bold.woff2",
)

PAIRES = (
    ("#1a1916", "#f6f5f2"),
    ("#1d4a38", "#ffffff"),
    ("#1d4a38", "#eef3ef"),
    ("#1d4a38", "#f7f1e6"),
    ("#1a1916", "#eef3ef"),
    ("#1a1916", "#f7f1e6"),
    ("#1d4a38", "#f6f5f2"),
    ("#f6f5f2", "#1a1916"),
    ("#c9ddd2", "#1a1916"),
    ("#1a1916", "#efece6"),
    ("#3f3b36", "#f6f5f2"),
    ("#3f3b36", "#efece6"),
)

EXEMPLE_ATTENDU = {
    "tentes": 2,
    "accords": 2,
}

ORDRE_NATURES = ("deterministe", "pertinence", "vision", "geste", "restitution", "document")

MOIS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)

INTERDITS = (
    "disruptif",
    "solution",
    "garantie",
    "certifié",
    "certifie",
    "leaderboard",
    "badge",
    "gold",
    "conforme rgaa",
    "en quelques clics",
)

HORS_FILE = "4.13.1/lecteur-audio"


def echapper(texte: str) -> str:
    return (
        str(texte)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


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


def liste_et(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " et " + items[-1]


def mot_pages(nombre: int) -> str:
    mots = {1: "une page", 2: "deux pages", 3: "trois pages", 4: "quatre pages"}
    return mots.get(nombre, f"{nombre} pages")


def fait(fort: str, label: str) -> str:
    return f"<li><strong>{echapper(fort)}</strong> {echapper(label)}</li>"


def criteres_ouverts(echantillon: dict) -> list[str]:
    if echantillon.get("taux") is not None:
        return []
    motif = echantillon.get("taux_motif") or ""
    trouve = re.search(r"Critères applicables encore ouverts : ([0-9., ]+)\.", motif)
    if not trouve:
        raise RuntimeError("taux non publié sans liste de critères ouverts")
    return [morceau.strip() for morceau in trouve.group(1).split(",") if morceau.strip()]


def themes_de(index: dict, cas: list[dict]) -> list[dict]:
    par_test: dict[str, list[dict]] = {}
    for entree in cas:
        par_test.setdefault(entree["test"], []).append(entree)
    themes = []
    vus: list[int] = []
    for test in index["tests"]:
        numero = test["thematique"]
        if numero in vus:
            continue
        vus.append(numero)
        identifiants = [entree for entree in index["tests"] if entree["thematique"] == numero]
        avec = brouillon = sans = 0
        for entree in identifiants:
            locaux = par_test.get(entree["id"], [])
            if any(cas_local["statut"] == "revu" for cas_local in locaux):
                avec += 1
            elif locaux:
                brouillon += 1
            else:
                sans += 1
        themes.append(
            {
                "titre": test["thematique_titre"],
                "tests": len(identifiants),
                "avec": avec,
                "brouillon": brouillon,
                "sans": sans,
            }
        )
    return themes


def sans_protocole_ni_cas(index: dict, cas: list[dict]) -> int:
    presents = {entree["test"] for entree in cas}
    return sum(1 for test in index["tests"] if not test["protocole"] and test["id"] not in presents)


def brouillons_de_la_file(echantillon: dict, par_id: dict[str, dict]) -> list[dict]:
    vus: list[str] = []
    for releve in echantillon["releves"]:
        identifiant = releve["cas"]
        if identifiant in vus:
            continue
        if par_id[identifiant]["statut"] != "revu":
            vus.append(identifiant)
    trouves = [par_id[identifiant] for identifiant in vus]
    return sorted(trouves, key=lambda entree: (banc.cle_tri(entree["test"]), entree["id"]))


def groupe_file(entree: dict) -> str:
    _test, slug = entree["id"].split("/", 1)
    if entree["test"].startswith("3.2."):
        return "contraste"
    if slug.startswith("sans-"):
        return "absence"
    return "autres"


def ligne_file(entree: dict) -> str:
    if entree["statut"] != "brouillon":
        raise RuntimeError(f"{entree['id']} est cité par la vitrine sans être un brouillon")
    test, slug = entree["id"].split("/", 1)
    href = f"cas/rgaa-4.1.2/{test}/{slug}/page.html"
    titre = entree["titre"].replace("'", APOS)
    return (
        "<tr>"
        "<td>Brouillon</td>"
        f'<td><a href="{href}"><code>{echapper(entree["id"])}</code></a></td>'
        f"<td>{echapper(titre)}</td>"
        f"<td>{LIBELLES[entree['verdict']]}</td>"
        "</tr>"
    )


def bloc_file(titre: str, caption: str, lignes: list[str]) -> str:
    if not lignes:
        return ""
    corps = "\n".join(lignes)
    return (
        f"<h3>{titre}</h3>\n"
        '<div class="defile" tabindex="0">\n'
        '<p class="annonce si-etroit">Sur un écran étroit, ce tableau se parcourt horizontalement.</p>\n'
        "<table>\n"
        f"<caption>{caption}</caption>\n"
        "<thead><tr>"
        '<th scope="col">Statut</th><th scope="col">Cas</th>'
        '<th scope="col">Page</th><th scope="col">Verdict proposé</th>'
        "</tr></thead>\n"
        f"<tbody>\n{corps}\n</tbody>\n"
        "</table>\n"
        "</div>"
    )


def carte_taux(echantillon: dict) -> tuple[str, str]:
    if echantillon.get("taux") is None:
        return "Non publié", "taux de la vitrine"
    texte = f"{echantillon['taux']}".replace(".", ",")
    return texte, "taux de la vitrine"


def carte_restitution(nombre: int) -> tuple[str, str]:
    if nombre == 0:
        return "Aucune", "restitution revue"
    if nombre == 1:
        return "1", "restitution revue"
    return str(nombre), "restitutions revues"


def date_fr(iso: str) -> str:
    annee, mois, jour = iso.split("-")
    return f"{int(jour)} {MOIS[int(mois) - 1]} {annee}"


def dates_relecture(cas: list[dict]) -> list[str]:
    return sorted(
        {
            entree["relecture"]
            for entree in cas
            if entree["statut"] == "revu" and entree.get("relecture")
        }
    )


def phrase_relecture(cas: list[dict]) -> str:
    dates = dates_relecture(cas)
    if not dates:
        return "Aucun cas revu n" + APOS + "a de date de relecture."
    if len(dates) == 1:
        return "La relecture du lot déjà revu date du " + date_fr(dates[0]) + "."
    return "La relecture du lot déjà revu va du " + date_fr(dates[0]) + " au " + date_fr(dates[-1]) + "."


def date_couverture(cas: list[dict]) -> str:
    dates = dates_relecture(cas)
    if not dates:
        return "à l" + APOS + "état du dépôt"
    return "au " + date_fr(dates[-1])


def html_natures(compte: dict, cas: list[dict]) -> str:
    if set(ORDRE_NATURES) != set(banc.NATURES):
        raise RuntimeError("ordre d'affichage des natures désaligné")
    textes = {
        "deterministe": ("Déterministe", "HTML ou CSS, là où la méthode ferme le test."),
        "pertinence": ("Pertinence", "Comprendre un sens et le rapporter au test."),
        "vision": ("Vision", "Une capture, parce que le HTML ne suffit pas."),
        "geste": ("Geste", "L’état après l’action, avec le viewport ou le zoom noté."),
        "restitution": ("Restitution", "Produit, version, langue, système, transcription réelle."),
        "document": ("Document", "PDF ou fichier bureautique."),
    }
    revus = [entree for entree in cas if entree["statut"] == "revu"]
    lignes = []
    for nature in ORDRE_NATURES:
        nombre = compte["par_nature"][nature]
        non_tranches = sum(
            1 for entree in revus if entree["nature"] == nature and entree["verdict"] == "non_tranche"
        )
        titre, detail = textes[nature]
        if nature == "pertinence" and non_tranches:
            suite = "non tranché" if non_tranches == 1 else "non tranchés"
            detail = f"{detail} Dont {non_tranches} {suite}."
        fort = "Aucun" if nombre == 0 else str(nombre)
        lignes.append(
            f'<li><span class="compte">{echapper(fort)}</span>'
            f'<span class="nature">{echapper(titre)}</span> {echapper(detail)}</li>'
        )
    return "\n".join(lignes)


def html_silence(accords: int, abstentions: int, silences: int) -> str:
    if accords == 1:
        ligne_accords = "<li><strong>1</strong> cas tenté, en accord</li>"
    else:
        ligne_accords = f"<li><strong>{accords}</strong> cas tentés, en accord</li>"
    if abstentions == 1:
        ligne_abs = "<li><strong>1</strong> abstention, sur un cas non tranché</li>"
    else:
        ligne_abs = f"<li><strong>{abstentions}</strong> abstentions, sur des cas non tranchés</li>"
    if silences == 1:
        ligne_sil = "<li><strong>1</strong> silence, hors du calcul</li>"
    else:
        ligne_sil = f"<li><strong>{silences}</strong> silences, hors du calcul</li>"
    return ligne_accords + ligne_abs + ligne_sil


def html_themes(themes: list[dict]) -> str:
    lignes = []
    for theme in themes:
        lignes.append(
            "<tr>"
            f'<th scope="row">{echapper(theme["titre"])}</th>'
            f'<td class="n">{theme["tests"]}</td>'
            f'<td class="n">{theme["avec"]}</td>'
            f'<td class="n">{theme["brouillon"]}</td>'
            f'<td class="n">{theme["sans"]}</td>'
            "</tr>"
        )
    return "\n".join(lignes)


def html_tiroirs(themes: list[dict]) -> str:
    lignes = []
    for theme in themes:
        if theme["avec"]:
            mot = "Quelques cas revus"
            detail = (
                f'{theme["avec"]} test sur {theme["tests"]}'
                if theme["avec"] == 1
                else f'{theme["avec"]} tests sur {theme["tests"]}'
            )
        elif theme["brouillon"] == 1:
            mot = "Un brouillon, aucun cas revu"
            detail = f'{theme["tests"]} tests' if theme["tests"] != 1 else "1 test"
        elif theme["brouillon"] > 1:
            mot = "Des brouillons, aucun cas revu"
            detail = f'{theme["tests"]} tests'
        else:
            mot = "Vide"
            detail = (
                f'{theme["tests"]} tests, aucun cas'
                if theme["tests"] != 1
                else "1 test, aucun cas"
            )
        lignes.append(
            f'<li><span class="mot">{echapper(mot)}</span>'
            f'<strong>{echapper(theme["titre"])}</strong>'
            f"<span>{echapper(detail)}</span></li>"
        )
    return "\n".join(lignes)


def phrase_file(nombre: int, ouverts: list[str], taux) -> str:
    if taux is not None:
        return (
            "Le taux de l" + APOS + "échantillon vitrine est publié. "
            "En relire un brouillon ne change pas ce taux. "
            "Le taux n" + APOS + "est pas l" + APOS + "accord des prédictions."
        )
    bloquent = "brouillon bloque" if nombre == 1 else "brouillons bloquent"
    return (
        f"{nombre} {bloquent} le taux de l" + APOS + "échantillon vitrine. "
        f"Les critères encore ouverts sont {liste_et(ouverts)}. "
        "En relire un seul ne ferme pas le critère. Le taux reste non publié."
    )


def phrase_taux_mesure(ouverts: list[str], taux) -> str:
    if taux is not None:
        return (
            "Le taux de la vitrine est publié. "
            "Il n" + APOS + "est pas l" + APOS + "accord des prédictions."
        )
    return (
        "Le taux de la vitrine, non publié tant que les critères "
        f"{liste_et(ouverts)} restent ouverts, n" + APOS + "est pas l" + APOS + "accord des prédictions."
    )


def phrase_themes(tests_revus: int, revus: int, sans: int) -> str:
    if tests_revus == 0:
        debut = "Aucun test n" + APOS + "a de cas revu."
    elif tests_revus == 1:
        debut = "1 test a au moins un cas revu."
    else:
        debut = f"{tests_revus} tests ont au moins un cas revu."
    if sans == 0:
        fin = "Chaque test a un protocole ou un cas."
    elif sans == 1:
        fin = "1 test n" + APOS + "a ni protocole ni cas."
    else:
        fin = f"{sans} tests n" + APOS + "ont ni protocole ni cas."
    return (
        f"{debut} Cela fait {revus} cas, pas {revus} tests couverts. "
        f"Un test revu ne couvre pas sa thématique. {fin}"
    )


def phrase_deux_chiffres(revus: int, tests: int, themes: list[dict]) -> str:
    vides = sum(1 for theme in themes if theme["avec"] == 0)
    if vides > len(themes) / 2:
        suite = "La plupart des thématiques n" + APOS + "ont aucun cas revu."
    elif vides == 0:
        suite = "Chaque thématique a au moins un cas revu. Cela ne la couvre pas."
    elif vides == 1:
        suite = "Une thématique n" + APOS + "a aucun cas revu."
    else:
        suite = f"{vides} thématiques n" + APOS + "ont aucun cas revu."
    return f"{revus} cas revus, pour {tests} tests. {suite}"


def phrase_exemple(resultat: dict, predictions: list[dict], cas: list[dict]) -> str:
    par_prediction = {prediction.get("cas"): prediction.get("verdict") for prediction in predictions}
    ouverts = [
        entree
        for entree in cas
        if entree["statut"] == "revu" and entree["verdict"] == "non_tranche"
    ]
    explicites = [entree for entree in ouverts if par_prediction.get(entree["id"]) == "non_tranche"]
    muets = [entree for entree in ouverts if entree["id"] not in par_prediction]
    tranches = [
        entree
        for entree in ouverts
        if entree["id"] in par_prediction and par_prediction[entree["id"]] not in (None, "non_tranche")
    ]
    if len(explicites) + len(muets) != resultat["abstentions"]:
        raise RuntimeError("les abstentions de l'exemple ne se répartissent pas")
    if len(tranches) != resultat["tranchages"]:
        raise RuntimeError("les tranchages de l'exemple ne se répartissent pas")
    tentes = resultat["tentes"]
    accords = resultat["accords"]
    if tentes == 0:
        debut = "L" + APOS + "exemple ne tente aucun cas tranché."
    elif accords == tentes and tentes == 1:
        debut = "L" + APOS + "exemple est d" + APOS + "accord sur le cas tranché qu" + APOS + "il tente."
    elif accords == tentes:
        debut = "L" + APOS + f"exemple est d{APOS}accord sur les {tentes} cas tranchés qu{APOS}il tente."
    else:
        debut = "L" + APOS + f"exemple tente {tentes} cas tranchés et en accorde {accords}."
    if not explicites and not muets:
        milieu = "Il ne s" + APOS + "abstient sur aucun cas non tranché."
    elif explicites and not muets:
        if len(explicites) == 1:
            milieu = (
                "Il s" + APOS + "abstient sur le cas non tranché, "
                "par une prédiction au verdict non tranché."
            )
        else:
            milieu = (
                f"Il s{APOS}abstient sur {len(explicites)} cas non tranchés, "
                "par des prédictions au verdict non tranché."
            )
    elif muets and not explicites:
        if len(muets) == 1:
            milieu = (
                "Il s" + APOS + "abstient sur le cas non tranché"
                + NNBSP + ": il n" + APOS + "en dit rien, "
                "et le scoreur compte ce silence comme une abstention."
            )
        else:
            milieu = (
                f"Il s{APOS}abstient sur {len(muets)} cas non tranchés"
                + NNBSP + ": il n" + APOS + "en dit rien, "
                "et le scoreur compte ces silences comme des abstentions."
            )
    else:
        if len(explicites) == 1:
            predit = "1 prédiction au verdict non tranché"
        else:
            predit = f"{len(explicites)} prédictions au verdict non tranché"
        if len(muets) == 1:
            tait = "1 silence que le scoreur compte comme une abstention"
        else:
            tait = f"{len(muets)} silences que le scoreur compte comme des abstentions"
        milieu = (
            f"Il s{APOS}abstient sur {len(explicites) + len(muets)} cas non tranchés"
            + NNBSP + ": " + liste_et([predit, tait]) + "."
        )
    if tranches:
        if len(tranches) == 1:
            milieu += (
                " Il tranche un cas non tranché"
                + NNBSP + ": cela n" + APOS + "augmente ni l" + APOS + "accord ni l" + APOS + "erreur."
            )
        else:
            milieu += (
                f" Il tranche {len(tranches)} cas non tranchés"
                + NNBSP + ": cela n" + APOS + "augmente ni l" + APOS + "accord ni l" + APOS + "erreur."
            )
    silences = resultat["silences"]
    if silences == 0:
        fin = "Il ne se tait sur aucun cas tranché."
    elif silences == 1:
        fin = "Il se tait sur 1 cas tranché."
    else:
        fin = f"Il se tait sur {silences} cas tranchés."
    return f"{debut} {milieu} {fin} Ce n{APOS}est pas une mesure du référentiel."


def phrase_pas_mesure(accords: int, silences: int) -> str:
    morceaux = []
    if accords == 1:
        morceaux.append("1 accord")
    elif accords:
        morceaux.append(f"{accords} accords")
    if silences == 1:
        morceaux.append("1 silence")
    elif silences:
        morceaux.append(f"{silences} silences")
    if not morceaux:
        return "Aucune tentative ne mesure le référentiel."
    if len(morceaux) == 1:
        verbe = "ne mesure pas" if morceaux[0].startswith("1 ") else "ne mesurent pas"
        return f"{morceaux[0]} {verbe} le référentiel."
    return f"{morceaux[0]} et {morceaux[1]} ne mesurent pas le référentiel."


def html_cas_non_tranches(cas: list[dict]) -> str:
    ouverts = sorted(
        (
            entree
            for entree in cas
            if entree["statut"] == "revu" and entree["verdict"] == "non_tranche"
        ),
        key=lambda entree: (banc.cle_tri(entree["test"]), entree["id"]),
    )
    if not ouverts:
        return "Aucun cas revu n" + APOS + "est non tranché"
    codes = [f"<code>{echapper(entree['id'])}</code>" for entree in ouverts]
    if len(codes) == 1:
        return "Le cas est " + codes[0]
    return "Les cas sont " + liste_et(codes)


def phrase_vitrine(echantillon: dict, ouverts: list[str], brouillons_file: int) -> str:
    pages = mot_pages(len(echantillon["pages"]))
    if echantillon.get("taux") is not None:
        return (
            "L" + APOS + f"échantillon vitrine est un service fictif{NNBSP}: {pages} "
            "d" + APOS + "archives municipales. Le taux publié n" + APOS
            + "est pas l" + APOS + "accord des prédictions."
        )
    bloquent = "brouillon les bloque" if brouillons_file == 1 else "brouillons les bloquent"
    return (
        "L" + APOS + f"échantillon vitrine est un service fictif{NNBSP}: {pages} "
        "d" + APOS + "archives municipales, au taux non publié. "
        f"Les critères {liste_et(ouverts)} restent ouverts, "
        f"{brouillons_file} {bloquent}, et ce vide n" + APOS + "est ni un zéro ni un oubli."
    )


def faits_accueil(compte: dict, echantillon: dict) -> str:
    fort, label = carte_restitution(compte["par_nature"]["restitution"])
    taux_fort, taux_label = carte_taux(echantillon)
    brouillons = compte["brouillons"]
    if brouillons == 0:
        carte_brouillon = fait("Aucun", "brouillon hors du compte")
    elif brouillons == 1:
        carte_brouillon = fait("1", "brouillon hors du compte")
    else:
        carte_brouillon = fait(str(brouillons), "brouillons hors du compte")
    revus = compte["revus"]
    carte_revus = fait("Aucun", "cas revu") if revus == 0 else fait(str(revus), "cas revu" if revus == 1 else "cas revus")
    return "".join(
        [
            carte_revus,
            carte_brouillon,
            fait(fort, label),
            fait(taux_fort, taux_label),
        ]
    )


def faits_mesurer(compte: dict, echantillon: dict) -> str:
    taux_fort, taux_label = carte_taux(echantillon)
    non_tranches = compte["non_tranches"]
    if non_tranches == 0:
        carte_ouverts = fait("Aucun", "cas revu non tranché")
    elif non_tranches == 1:
        carte_ouverts = fait("1", "cas revu non tranché")
    else:
        carte_ouverts = fait(str(non_tranches), "cas revus non tranchés")
    brouillons = compte["brouillons"]
    label_brouillons = "brouillon hors du compte" if brouillons == 1 else "brouillons hors du compte"
    protocoles = compte["protocoles"]
    label_protocoles = "test a un protocole" if protocoles == 1 else "tests ont un protocole"
    revus = compte["revus"]
    return "".join(
        [
            fait(str(compte["tests"]), "tests"),
            fait(str(compte["criteres"]), "critères"),
            fait(str(protocoles), label_protocoles),
            fait(str(revus), "cas revu" if revus == 1 else "cas revus"),
            fait(str(brouillons), label_brouillons),
            carte_ouverts,
            fait(taux_fort, taux_label),
        ]
    )


def pastilles(compte: dict, tests_revus: int) -> str:
    protocoles = compte["protocoles"]
    brouillons = compte["brouillons"]
    return "".join(
        [
            fait(str(protocoles), "test a un protocole" if protocoles == 1 else "tests ont un protocole"),
            fait(
                str(brouillons),
                "brouillon hors du compte" if brouillons == 1 else "brouillons hors du compte",
            ),
            fait(
                str(tests_revus),
                "test a au moins un cas revu" if tests_revus == 1 else "tests ont au moins un cas revu",
            ),
        ]
    )


def lire_exemple(modele: str) -> dict:
    trouve = re.search(r'<pre id="json-exemple".*?<code>(.*?)</code>', modele, re.S)
    if not trouve:
        raise RuntimeError("exemple JSON absent du modèle")
    return json.loads(trouve.group(1))


def verifier_polices() -> None:
    dossier = banc.RACINE / "polices"
    for nom in POLICES:
        if not (dossier / nom).is_file():
            raise RuntimeError(f"police absente : polices/{nom}")


def verifier_contraste() -> None:
    for avant, arriere in PAIRES:
        if rapport(avant, arriere) < 4.5:
            raise RuntimeError(f"contraste insuffisant {avant} sur {arriere}")


def verifier_liens(html: str, par_id: dict[str, dict]) -> None:
    for test, slug in re.findall(r"cas/rgaa-4\.1\.2/(\d+\.\d+\.\d+)/([a-z0-9-]+)/page\.html", html):
        if not (banc.CHEMIN_CAS / test / slug / "page.html").is_file():
            raise RuntimeError(f"page absente : {test}/{slug}")
    for test in re.findall(r"site/protocoles/(\d+\.\d+\.\d+)\.html", html):
        if not (banc.CHEMIN_PROTOCOLES / f"{test}.md").is_file():
            raise RuntimeError(f"protocole absent : {test}")
    for bloc in re.findall(r'<div class="cas">(.*?)</div>', html, re.S):
        liens = re.findall(r"cas/rgaa-4\.1\.2/(\d+\.\d+\.\d+)/([a-z0-9-]+)/page\.html", bloc)
        if not liens:
            if "Pas de cas" not in bloc:
                raise RuntimeError("carte sans cas et sans mention d'absence")
            continue
        identifiant = f"{liens[0][0]}/{liens[0][1]}"
        entree = par_id[identifiant]
        if f">{LIBELLES[entree['statut']]}</span>" not in bloc:
            raise RuntimeError(f"{identifiant} : le statut n'est pas écrit avant le verdict")
        if entree["statut"] == "revu" and f"</span> {LIBELLES[entree['verdict']]}" not in bloc:
            raise RuntimeError(f"{identifiant} : le verdict relu n'est pas écrit")
    if "1.1.1" not in {entree["test"] for entree in par_id.values()}:
        if "Pas de cas, pas de protocole." not in html:
            raise RuntimeError("le test 1.1.1 a changé, la vitrine doit le dire")
    if (banc.CHEMIN_PROTOCOLES / "1.1.1.md").is_file() or any(
        entree["test"] == "1.1.1" for entree in par_id.values()
    ):
        raise RuntimeError("1.1.1 n'est plus vide, la vitrine doit être réécrite")
    transcription = banc.CHEMIN_CAS / "4.13.1" / "lecteur-audio" / "transcription.txt"
    if not transcription.is_file() or "EXEMPLE" not in transcription.read_text(encoding="utf-8"):
        raise RuntimeError("la transcription de 4.13.1 ne contient plus EXEMPLE")
    image = banc.CHEMIN_CAS / "3.2.1" / "texte-en-image" / "texte.png"
    if not image.is_file():
        raise RuntimeError("capture texte-en-image absente")


def verifier_hors_file(cas: list[dict], file: list[dict]) -> None:
    cites = {entree["id"] for entree in file}
    hors = sorted(entree["id"] for entree in cas if entree["statut"] == "brouillon" and entree["id"] not in cites)
    if hors != [HORS_FILE]:
        raise RuntimeError(f"brouillons hors file inattendus : {', '.join(hors)}")


def rendre() -> str:
    verifier_polices()
    verifier_contraste()
    if not MODELE.is_file():
        raise RuntimeError("modèle de vitrine absent")
    modele = MODELE.read_text(encoding="utf-8")
    index = banc.charger_index()
    cas = banc.charger_cas()
    par_id = {entree["id"]: entree for entree in cas}
    echantillon = banc.lire_json(banc.CHEMIN_ECHANTILLON)
    compte = banc.compte_couverture(cas, index)
    themes = themes_de(index, cas)
    ouverts = criteres_ouverts(echantillon)
    file = brouillons_de_la_file(echantillon, par_id)
    verifier_hors_file(cas, file)
    tests_revus = sum(theme["avec"] for theme in themes)
    sans = sans_protocole_ni_cas(index, cas)
    exemple = lire_exemple(modele)
    resultat = banc.resultat_score(exemple["outil"], exemple["date"], exemple["predictions"], cas)
    if resultat["erreurs"]:
        raise RuntimeError("exemple de prédiction illisible : " + "; ".join(resultat["erreurs"]))
    if (
        resultat["tentes"] != EXEMPLE_ATTENDU["tentes"]
        or resultat["accords"] != EXEMPLE_ATTENDU["accords"]
    ):
        raise RuntimeError(
            "l'exemple illustré ne mesure plus "
            f"{EXEMPLE_ATTENDU['tentes']} cas tentés et {EXEMPLE_ATTENDU['accords']} accords"
        )
    image = par_id.get("3.2.1/texte-en-image")
    if not image or image["statut"] != "revu" or not image.get("relecture"):
        raise RuntimeError("3.2.1/texte-en-image n'a plus de relecture à citer")
    groupes = {"absence": [], "contraste": [], "autres": []}
    for entree in file:
        groupes[groupe_file(entree)].append(ligne_file(entree))
    jetons = {
        "@@FAITS_ACCUEIL@@": faits_accueil(compte, echantillon),
        "@@FAITS_MESURER@@": faits_mesurer(compte, echantillon),
        "@@NATURES@@": html_natures(compte, cas),
        "@@SILENCE@@": html_silence(resultat["accords"], resultat["abstentions"], resultat["silences"]),
        "@@THEMATIQUES@@": html_themes(themes),
        "@@TIROIRS@@": html_tiroirs(themes),
        "@@PASTILLES@@": pastilles(compte, tests_revus),
        "@@BLOC_ABSENCE@@": bloc_file(
            f"Au navigateur{NNBSP}: l{APOS}élément visé est absent",
            "Brouillons d" + APOS + "absence. Le verdict proposé ne se cite pas.",
            groupes["absence"],
        ),
        "@@BLOC_CONTRASTE@@": bloc_file(
            f"Au navigateur{NNBSP}: contraste, taille, graisse",
            "Brouillons de contraste. Le verdict proposé ne se cite pas.",
            groupes["contraste"],
        ),
        "@@BLOC_AUTRES@@": bloc_file(
            "Autres brouillons de la file",
            "Autres brouillons cités par la vitrine. Le verdict proposé ne se cite pas.",
            groupes["autres"],
        ),
        "@@PHRASE_FILE@@": echapper(phrase_file(len(file), ouverts, echantillon.get("taux"))),
        "@@PHRASE_TAUX_MESURE@@": echapper(phrase_taux_mesure(ouverts, echantillon.get("taux"))),
        "@@PHRASE_THEMES@@": echapper(phrase_themes(tests_revus, compte["revus"], sans)),
        "@@PHRASE_DEUX_CHIFFRES@@": echapper(phrase_deux_chiffres(compte["revus"], compte["tests"], themes)),
        "@@PHRASE_VITRINE@@": echapper(phrase_vitrine(echantillon, ouverts, len(file))),
        "@@PHRASE_EXEMPLE@@": echapper(phrase_exemple(resultat, exemple["predictions"], cas)),
        "@@PHRASE_PAS_MESURE@@": echapper(phrase_pas_mesure(resultat["accords"], resultat["silences"])),
        "@@PHRASE_RELECTURE@@": echapper(phrase_relecture(cas)),
        "@@CAS_NON_TRANCHES@@": html_cas_non_tranches(cas),
        "@@DATE_COUVERTURE@@": echapper(date_couverture(cas)),
        "@@DATE_TEXTE_IMAGE@@": echapper(date_fr(image["relecture"])),
        "@@TESTS@@": str(compte["tests"]),
        "@@CRITERES@@": str(compte["criteres"]),
        "@@NB_THEMES@@": str(len(themes)),
        "@@REVUS@@": str(compte["revus"]),
    }
    html = modele
    for jeton, valeur in jetons.items():
        if jeton not in html:
            raise RuntimeError(f"jeton absent du modèle : {jeton}")
        html = html.replace(jeton, valeur)
    reste = re.findall(r"@@[A-Z_]+@@", html)
    if reste:
        raise RuntimeError("jeton non remplacé : " + ", ".join(reste))
    if compte["par_nature"]["restitution"] or compte["par_nature"]["document"]:
        raise RuntimeError("un cas de restitution ou de document est revu : réécrire l'encart")
    if any(entree["nature"] == "document" for entree in cas):
        raise RuntimeError("un cas document existe : réécrire l'encart")
    verifier_liens(html, par_id)
    verifier_cartes(html, cas)
    verifier_mots(html)
    return html


def verifier_cartes(html: str, cas: list[dict]) -> None:
    for test, corps in re.findall(r'<article data-test="([^"]+)">(.*?)</article>', html, re.S):
        liens = {
            f"{test}/{slug}"
            for slug in re.findall(
                r"cas/rgaa-4\.1\.2/" + re.escape(test) + r"/([a-z0-9-]+)/page\.html",
                corps,
            )
        }
        depot = {entree["id"] for entree in cas if entree["test"] == test}
        if test == "1.1.1":
            if depot:
                raise RuntimeError("1.1.1 a un cas, la carte doit être réécrite")
            continue
        if liens != depot:
            raise RuntimeError(f"{test} : la carte n'illustre pas les mêmes cas que le dépôt")
    cites = {
        entree["id"]
        for entree in cas
        if entree["statut"] == "revu" and entree["verdict"] == "non_tranche"
    }
    attendus = {"6.1.1/lire-la-suite-sous-article", "8.6.1/titre-contact-seul"}
    if cites != attendus or "L’autre cas non tranché du lot est" not in html:
        raise RuntimeError("la phrase sur l'autre cas non tranché doit être réécrite")


def verifier_mots(html: str) -> None:
    visible = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<[^>]+>", " ", visible)
    bas = visible.casefold()
    for mot in INTERDITS:
        if re.search(r"\b" + re.escape(mot) + r"\b", bas):
            raise RuntimeError(f"mot interdit dans la vitrine : {mot}")
    if re.search(r"\bIA\b", visible):
        raise RuntimeError("mot interdit dans la vitrine : IA")
    if re.search(r"\bsimple\b", bas):
        raise RuntimeError("mot interdit dans la vitrine : simple")
