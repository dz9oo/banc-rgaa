"""Contrat du banc d'essai RGAA. Bibliothèque standard seule."""

from __future__ import annotations

import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_INDEX = RACINE / "referentiel" / "rgaa-4.1.2" / "index.json"
CHEMIN_CRITERES = RACINE / "referentiel" / "rgaa-4.1.2" / "criteres.json"
CHEMIN_CAS = RACINE / "cas" / "rgaa-4.1.2"
CHEMIN_PROTOCOLES = RACINE / "protocoles" / "rgaa-4.1.2"
CHEMIN_ECHANTILLON = RACINE / "echantillons" / "vitrine" / "echantillon.json"
CHEMIN_README = RACINE / "README.md"

VERDICTS = ("conforme", "non_conforme", "non_applicable", "non_tranche")
VERDICTS_TRANCHES = ("conforme", "non_conforme", "non_applicable")
NATURES = ("deterministe", "pertinence", "vision", "restitution", "geste", "document")
MODALITES = ("html", "capture", "transcription", "interaction", "document")
STATUTS = ("brouillon", "revu")
LICENCES = ("etalab-2.0", "w3c-document")

CLEFS_CAS = {
    "id",
    "referentiel",
    "version",
    "test",
    "titre",
    "verdict",
    "nature",
    "modalites",
    "motif",
    "methode",
    "statut",
    "fichiers",
    "licence",
    "origine",
    "cibles",
    "environnement",
    "pieges",
    "desaccords",
    "relecture",
    "note",
}
OBLIGATOIRES_CAS = {
    "id",
    "referentiel",
    "version",
    "test",
    "titre",
    "verdict",
    "nature",
    "modalites",
    "motif",
    "methode",
    "statut",
    "fichiers",
    "licence",
    "origine",
}


def lire_json(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8"))


def ecrire_json(chemin: Path, donnees) -> None:
    chemin.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def cle_tri(identifiant: str) -> tuple:
    return tuple(int(morceau) for morceau in identifiant.split("."))


def intitule_lisible(texte: str) -> str:
    texte = texte.replace("\u00a0", " ")
    texte = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texte)
    texte = texte.replace("`", "")
    texte = re.sub(r"[ \t]+", " ", texte)
    return texte.strip()


def methode_du_test(identifiant: str) -> str:
    return (
        "https://accessibilite.numerique.gouv.fr/methode/criteres-et-tests/#"
        + identifiant
    )


def construire_index() -> dict:
    brut = lire_json(CHEMIN_CRITERES)
    tests = []
    criteres = []
    for thematique in brut["topics"]:
        numero = thematique["number"]
        for enveloppe in thematique["criteria"]:
            critere = enveloppe["criterium"]
            identifiant = f"{numero}.{critere['number']}"
            criteres.append(identifiant)
            for numero_test, lignes in critere["tests"].items():
                tests.append(
                    {
                        "id": f"{identifiant}.{numero_test}",
                        "critere": identifiant,
                        "thematique": numero,
                        "thematique_titre": thematique["topic"],
                        "intitule": intitule_lisible(lignes[0]),
                        "critere_intitule": intitule_lisible(critere["title"]),
                        "methode": methode_du_test(f"{identifiant}.{numero_test}"),
                    }
                )
    tests.sort(key=lambda entree: cle_tri(entree["id"]))
    protocoles = {}
    if CHEMIN_PROTOCOLES.is_dir():
        for chemin in CHEMIN_PROTOCOLES.glob("*.md"):
            protocoles[chemin.stem] = f"protocoles/rgaa-4.1.2/{chemin.name}"
    for entree in tests:
        entree["protocole"] = protocoles.get(entree["id"])
    return {
        "referentiel": "RGAA",
        "version": "4.1.2",
        "source": "referentiel/rgaa-4.1.2/criteres.json",
        "critere_compte": len(criteres),
        "test_compte": len(tests),
        "tests": tests,
    }


def tests_par_id(index: dict) -> dict:
    return {entree["id"]: entree for entree in index["tests"]}


def tests_du_critere(index: dict, critere: str) -> list:
    return [entree for entree in index["tests"] if entree["critere"] == critere]


def ecrire_index() -> dict:
    index = construire_index()
    ecrire_json(CHEMIN_INDEX, index)
    return index


def charger_index() -> dict:
    return lire_json(CHEMIN_INDEX)


def index_a_jour() -> list[str]:
    if not CHEMIN_INDEX.is_file():
        return ["index.json absent"]
    frais = construire_index()
    enregistre = charger_index()
    if frais != enregistre:
        return ["index.json ne correspond pas à criteres.json et aux protocoles"]
    erreurs = []
    if enregistre["critere_compte"] != 106:
        erreurs.append(f"critères : {enregistre['critere_compte']}, attendu 106")
    if enregistre["test_compte"] != 258:
        erreurs.append(f"tests : {enregistre['test_compte']}, attendu 258")
    return erreurs


def dossiers_cas() -> list[Path]:
    if not CHEMIN_CAS.is_dir():
        return []
    return sorted(chemin for chemin in CHEMIN_CAS.glob("*/*") if (chemin / "cas.json").is_file())


def charger_cas() -> list[dict]:
    charges = []
    for dossier in dossiers_cas():
        donnees = lire_json(dossier / "cas.json")
        donnees["_dossier"] = dossier
        charges.append(donnees)
    return charges


def _ajouter(erreurs: list[str], message: str) -> None:
    erreurs.append(message)


def erreurs_cas(dossier: Path, index: dict) -> list[str]:
    erreurs: list[str] = []
    chemin = dossier / "cas.json"
    if not chemin.is_file():
        return [f"{dossier} : cas.json absent"]
    try:
        cas = lire_json(chemin)
    except json.JSONDecodeError as exc:
        return [f"{chemin} : JSON illisible ({exc})"]
    if not isinstance(cas, dict):
        return [f"{chemin} : objet JSON attendu"]
    try:
        relatif = str(dossier.relative_to(RACINE))
    except ValueError:
        relatif = str(dossier)
    inconnues = sorted(set(cas) - CLEFS_CAS)
    if inconnues:
        _ajouter(erreurs, f"{relatif} : clefs inconnues {', '.join(inconnues)}")
    manquantes = sorted(OBLIGATOIRES_CAS - set(cas))
    if manquantes:
        _ajouter(erreurs, f"{relatif} : clefs manquantes {', '.join(manquantes)}")
        return erreurs
    identifiant = cas["id"]
    if not isinstance(identifiant, str) or "/" not in identifiant:
        _ajouter(erreurs, f"{relatif} : id invalide")
        return erreurs
    test, slug = identifiant.split("/", 1)
    if dossier.parent.name != test or dossier.name != slug:
        _ajouter(erreurs, f"{relatif} : le chemin ne reprend pas l'id {identifiant}")
    if not re.fullmatch(r"[a-z0-9-]{3,48}", slug):
        _ajouter(erreurs, f"{identifiant} : slug hors format")
    if cas["referentiel"] != "RGAA" or cas["version"] != "4.1.2":
        _ajouter(erreurs, f"{identifiant} : référentiel ou version inattendus")
    if cas["test"] != test:
        _ajouter(erreurs, f"{identifiant} : le champ test ne vaut pas {test}")
    connu = tests_par_id(index).get(test)
    if connu is None:
        _ajouter(erreurs, f"{identifiant} : test absent de l'index")
    if cas["verdict"] not in VERDICTS:
        _ajouter(erreurs, f"{identifiant} : verdict inconnu")
    if cas["nature"] not in NATURES:
        _ajouter(erreurs, f"{identifiant} : nature inconnue")
    if cas["statut"] not in STATUTS:
        _ajouter(erreurs, f"{identifiant} : statut inconnu")
    if cas["licence"] not in LICENCES:
        _ajouter(erreurs, f"{identifiant} : licence inconnue")
    if not isinstance(cas["titre"], str) or not 8 <= len(cas["titre"]) <= 140:
        _ajouter(erreurs, f"{identifiant} : titre hors longueur")
    if not isinstance(cas["motif"], str) or not 80 <= len(cas["motif"]) <= 2000:
        _ajouter(erreurs, f"{identifiant} : motif hors des bornes 80 à 2000 caractères")
    url = methode_du_test(test)
    if cas["methode"] != url:
        _ajouter(erreurs, f"{identifiant} : methode doit valoir {url}")
    modalites = cas["modalites"]
    if (
        not isinstance(modalites, list)
        or not modalites
        or len(modalites) != len(set(modalites))
        or any(entree not in MODALITES for entree in modalites)
    ):
        _ajouter(erreurs, f"{identifiant} : modalites invalides")
    fichiers = cas["fichiers"]
    if not isinstance(fichiers, list) or not fichiers:
        _ajouter(erreurs, f"{identifiant} : fichiers vide")
        fichiers = []
    for nom in fichiers:
        if not isinstance(nom, str) or nom != Path(nom).name or nom == "cas.json":
            _ajouter(erreurs, f"{identifiant} : fichier illicite {nom}")
            continue
        if not (dossier / nom).is_file():
            _ajouter(erreurs, f"{identifiant} : fichier absent {nom}")
    if isinstance(fichiers, list):
        attendus = {"cas.json", *fichiers}
        presents = {chemin.name for chemin in dossier.iterdir() if chemin.is_file()}
        en_trop = presents - attendus
        if en_trop:
            _ajouter(erreurs, f"{identifiant} : fichiers non déclarés {', '.join(sorted(en_trop))}")
    origine = cas["origine"]
    if cas["licence"] == "w3c-document":
        if not isinstance(origine, dict) or not str(origine.get("url", "")).startswith("https://"):
            _ajouter(erreurs, f"{identifiant} : une adaptation W3C exige origine.url")
    elif origine != "original":
        _ajouter(erreurs, f"{identifiant} : origine attendue « original »")
    if cas["statut"] == "revu":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(cas.get("relecture", ""))):
            _ajouter(erreurs, f"{identifiant} : relecture AAAA-MM-JJ obligatoire pour un cas revu")
    environnement = cas.get("environnement")
    if environnement is not None and not isinstance(environnement, dict):
        _ajouter(erreurs, f"{identifiant} : environnement illisible")
        environnement = {}
    if cas["nature"] in ("vision", "geste"):
        navigateur = (environnement or {}).get("navigateur")
        if not isinstance(navigateur, str) or len(navigateur) < 3:
            _ajouter(erreurs, f"{identifiant} : navigateur obligatoire")
        if not any(str(nom).lower().endswith(".png") for nom in fichiers):
            _ajouter(erreurs, f"{identifiant} : capture PNG obligatoire")
    if cas["nature"] == "geste":
        env = environnement or {}
        if not env.get("viewport") and not env.get("zoom"):
            _ajouter(erreurs, f"{identifiant} : viewport ou zoom obligatoire")
    if cas["nature"] == "restitution" and cas["statut"] == "revu":
        env = environnement or {}
        if not env.get("technologie_assistance"):
            _ajouter(erreurs, f"{identifiant} : technologie d'assistance obligatoire")
        transcriptions = [nom for nom in fichiers if str(nom).endswith(".txt")]
        if not transcriptions:
            _ajouter(erreurs, f"{identifiant} : transcription obligatoire")
        for nom in transcriptions:
            texte = (dossier / nom).read_text(encoding="utf-8")
            if "EXEMPLE" in texte:
                _ajouter(erreurs, f"{identifiant} : transcription d'exemple, statut revu refusé")
    if cas["verdict"] == "non_tranche":
        desaccords = cas.get("desaccords")
        if not isinstance(desaccords, list) or len(desaccords) < 2:
            _ajouter(erreurs, f"{identifiant} : deux lectures au moins dans desaccords")
        else:
            for lecture in desaccords:
                if not isinstance(lecture, dict):
                    _ajouter(erreurs, f"{identifiant} : lecture illisible")
                    continue
                if set(lecture) - {"lecture", "motif"}:
                    _ajouter(erreurs, f"{identifiant} : clef inconnue dans desaccords")
                if not isinstance(lecture.get("lecture"), str) or len(lecture["lecture"]) < 8:
                    _ajouter(erreurs, f"{identifiant} : intitulé de lecture trop court")
                if not isinstance(lecture.get("motif"), str) or len(lecture["motif"]) < 40:
                    _ajouter(erreurs, f"{identifiant} : motif de lecture trop court")
    elif cas.get("desaccords"):
        _ajouter(erreurs, f"{identifiant} : desaccords réservés au verdict non_tranche")
    if "pieges" in cas:
        pieges = cas["pieges"]
        if not isinstance(pieges, list) or any(not isinstance(entree, str) or len(entree) < 20 for entree in pieges):
            _ajouter(erreurs, f"{identifiant} : pieges illisibles")
    if "cibles" in cas:
        cibles = cas["cibles"]
        if not isinstance(cibles, list):
            _ajouter(erreurs, f"{identifiant} : cibles illisibles")
        else:
            for cible in cibles:
                if not isinstance(cible, dict) or set(cible) != {"selecteur", "note"}:
                    _ajouter(erreurs, f"{identifiant} : cible incomplète")
    return erreurs


def decouper_protocole(texte: str) -> tuple[dict, str]:
    if not texte.startswith("---\n"):
        raise ValueError("front matter absent")
    fin = texte.find("\n---\n", 4)
    if fin == -1:
        raise ValueError("front matter non fermé")
    donnees = {}
    for ligne in texte[4:fin].splitlines():
        if not ligne.strip():
            continue
        if ":" not in ligne:
            raise ValueError(f"ligne sans clef : {ligne}")
        clef, valeur = ligne.split(":", 1)
        valeur = valeur.strip()
        if len(valeur) >= 2 and valeur[0] == '"' and valeur[-1] == '"':
            valeur = valeur[1:-1]
        donnees[clef.strip()] = valeur
    return donnees, texte[fin + 5 :]


def erreurs_protocole(chemin: Path, index: dict, cas: list[dict]) -> list[str]:
    erreurs: list[str] = []
    identifiant = chemin.stem
    try:
        meta, corps = decouper_protocole(chemin.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{identifiant} : {exc}"]
    attendues = {"test", "version", "nature", "methode", "machine", "personne"}
    if set(meta) != attendues:
        _ajouter(erreurs, f"{identifiant} : front matter {sorted(meta)} au lieu de {sorted(attendues)}")
        return erreurs
    if meta["test"] != identifiant:
        _ajouter(erreurs, f"{identifiant} : le front matter ne reprend pas le nom du fichier")
    if meta["version"] != "4.1.2":
        _ajouter(erreurs, f"{identifiant} : version inattendue")
    if meta["nature"] not in NATURES:
        _ajouter(erreurs, f"{identifiant} : nature inconnue")
    if identifiant not in tests_par_id(index):
        _ajouter(erreurs, f"{identifiant} : test absent de l'index")
    if meta["methode"] != methode_du_test(identifiant):
        _ajouter(erreurs, f"{identifiant} : methode inattendue")
    if meta["machine"].strip() == meta["personne"].strip():
        _ajouter(erreurs, f"{identifiant} : machine et personne disent la même chose")
    if len(meta["machine"]) < 40 or len(meta["personne"]) < 40:
        _ajouter(erreurs, f"{identifiant} : machine ou personne trop court")
    for titre in ("## Environnement", "## Ce qui se tranche", "## Pièges"):
        if titre not in corps:
            _ajouter(erreurs, f"{identifiant} : titre manquant {titre}")
    for entree in cas:
        if entree["test"] == identifiant and entree["id"] not in corps:
            _ajouter(erreurs, f"{identifiant} : le cas {entree['id']} n'est pas nommé")
    return erreurs


def _arrondi(part: int, total: int):
    if total == 0:
        return None
    valeur = (Decimal(part) * Decimal(100) / Decimal(total)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    if valeur == valeur.to_integral():
        return int(valeur)
    return float(valeur)


def _verdict_page(verdicts: list[str]) -> str:
    if any(verdict == "non_conforme" for verdict in verdicts):
        return "non_conforme"
    if any(verdict == "non_tranche" for verdict in verdicts):
        return "non_tranche"
    if verdicts and all(verdict == "non_applicable" for verdict in verdicts):
        return "non_applicable"
    return "conforme"


def agreger(echantillon: dict, index: dict, cas_revus: set[str] | None = None) -> dict:
    """Calcule la grille à partir des relevés. Ne lit aucun HTML.

    Si cas_revus est fourni, un relevé ne couvre le test que lorsque son cas y figure.
    None conserve le décompte de tous les relevés, utilisé par les essais internes.
    """

    def couvre(releve: dict) -> bool:
        if cas_revus is None:
            return True
        return releve.get("cas") in cas_revus

    pages = [page["id"] for page in echantillon["pages"]]
    meta = {page["id"]: page for page in echantillon["pages"]}
    connus = tests_par_id(index)
    manques_par_critere = {}
    verdicts_pages: dict[str, dict[str, str]] = {page: {} for page in pages}
    for critere in echantillon["perimetre"]:
        tests = tests_du_critere(index, critere)
        manques = []
        for test in tests:
            pages_couvertes = {
                releve["page"]
                for releve in echantillon["releves"]
                if releve["test"] == test["id"] and couvre(releve)
            }
            if pages_couvertes != set(pages):
                manques.append(test["id"])
        if manques:
            manques_par_critere[critere] = manques
            continue
        for page in pages:
            locaux = [
                releve["verdict"]
                for releve in echantillon["releves"]
                if releve["page"] == page
                and releve["test"] in connus
                and connus[releve["test"]]["critere"] == critere
                and couvre(releve)
            ]
            verdicts_pages[page][critere] = _verdict_page(locaux)
    groupes: dict[str, list[str]] = {}
    for page in pages:
        processus = meta[page].get("processus")
        if processus:
            groupes.setdefault(processus, []).append(page)
    for groupe in groupes.values():
        for critere in echantillon["perimetre"]:
            if critere in manques_par_critere:
                continue
            if any(verdicts_pages[page].get(critere) == "non_conforme" for page in groupe):
                for page in groupe:
                    if verdicts_pages[page].get(critere) == "conforme":
                        verdicts_pages[page][critere] = "non_conforme"
    criteres = []
    ouverts = []
    non_tranches = []
    for critere in sorted(echantillon["perimetre"], key=cle_tri):
        if critere in manques_par_critere:
            ouverts.append(critere)
            continue
        valeurs = [verdicts_pages[page][critere] for page in pages]
        if any(valeur == "non_tranche" for valeur in valeurs):
            verdict = "non_tranche"
            non_tranches.append(critere)
        elif any(valeur == "non_conforme" for valeur in valeurs):
            verdict = "non_conforme"
        elif any(valeur == "conforme" for valeur in valeurs):
            verdict = "conforme"
        else:
            verdict = "non_applicable"
        criteres.append(
            {
                "id": critere,
                "verdict": verdict,
                "couvert": True,
                "motif": "Tous les tests de ce critère ont un relevé sur chaque page.",
            }
        )
    if ouverts or non_tranches:
        morceaux = []
        if ouverts:
            morceaux.append(
                "Critères applicables encore ouverts : " + ", ".join(sorted(ouverts, key=cle_tri)) + "."
            )
        if non_tranches:
            morceaux.append(
                "Critères non tranchés : " + ", ".join(sorted(non_tranches, key=cle_tri)) + "."
            )
        taux = None
        motif = "Le taux n'est pas publié. " + " ".join(morceaux)
    else:
        conformes = sum(1 for entree in criteres if entree["verdict"] == "conforme")
        non_conformes = sum(1 for entree in criteres if entree["verdict"] == "non_conforme")
        if conformes + non_conformes == 0:
            taux = None
            motif = "Le taux n'est pas publié. Aucun critère du périmètre n'est applicable."
        else:
            taux = _arrondi(conformes, conformes + non_conformes)
            motif = (
                "Taux des critères conformes sur les critères applicables du périmètre, "
                "arrondi au dixième."
            )
    return {
        "criteres": criteres,
        "taux": taux,
        "taux_motif": motif,
        "detail_pages": verdicts_pages,
    }


def erreurs_echantillon(chemin: Path, index: dict) -> list[str]:
    if not chemin.is_file():
        return []
    erreurs: list[str] = []
    ech = lire_json(chemin)
    cas = {entree["id"]: entree for entree in charger_cas()}
    revus = {identifiant for identifiant, entree in cas.items() if entree["statut"] == "revu"}
    connus = tests_par_id(index)
    pages = {page["id"] for page in ech["pages"]}
    dossier = chemin.parent
    for page in ech["pages"]:
        fichier = dossier / page["fichier"]
        if not fichier.is_file():
            _ajouter(erreurs, f"{ech['id']} : page absente {page['fichier']}")
        if not page.get("motifs"):
            _ajouter(erreurs, f"{ech['id']} : motifs d'échantillon vides pour {page['id']}")
    vus = set()
    for releve in ech["releves"]:
        clef = (releve["page"], releve["test"])
        if clef in vus:
            _ajouter(erreurs, f"{ech['id']} : relevé doublé {clef}")
        vus.add(clef)
        if releve["page"] not in pages:
            _ajouter(erreurs, f"{ech['id']} : page inconnue {releve['page']}")
        if releve["test"] not in connus:
            _ajouter(erreurs, f"{ech['id']} : test inconnu {releve['test']}")
            continue
        if connus[releve["test"]]["critere"] not in ech["perimetre"]:
            _ajouter(erreurs, f"{ech['id']} : {releve['test']} hors périmètre")
        source = cas.get(releve["cas"])
        if source is None:
            _ajouter(erreurs, f"{ech['id']} : cas absent {releve['cas']}")
            continue
        if source["test"] != releve["test"] or source["verdict"] != releve["verdict"]:
            _ajouter(erreurs, f"{ech['id']} : le relevé {releve['cas']} ne reprend pas le cas")
    for critere in ech["perimetre"]:
        if not tests_du_critere(index, critere):
            _ajouter(erreurs, f"{ech['id']} : critère inconnu {critere}")
    calcul = agreger(ech, index, revus)
    for clef in ("criteres", "taux", "taux_motif"):
        if ech.get(clef) != calcul[clef]:
            _ajouter(erreurs, f"{ech['id']} : {clef} ne correspond pas au calcul")
    return erreurs


def resultat_score(outil: str, date: str, predictions: list[dict], cas: list[dict]) -> dict:
    par_id = {entree["id"]: entree for entree in cas}
    erreurs = []
    vues = set()
    retenues = {}
    for prediction in predictions:
        identifiant = prediction.get("cas")
        if identifiant in vues:
            erreurs.append(f"prédiction doublée : {identifiant}")
            continue
        vues.add(identifiant)
        if identifiant not in par_id:
            erreurs.append(f"cas inconnu : {identifiant}")
            continue
        if "verdict" in prediction and prediction["verdict"] not in VERDICTS:
            erreurs.append(f"verdict inconnu pour {identifiant}")
            continue
        retenues[identifiant] = prediction.get("verdict")
    tranches = [
        entree
        for entree in cas
        if entree["statut"] == "revu" and entree["verdict"] in VERDICTS_TRANCHES
    ]
    ouverts = [
        entree
        for entree in cas
        if entree["statut"] == "revu" and entree["verdict"] == "non_tranche"
    ]
    accords = 0
    tentes = 0
    silences = 0
    par_nature: dict[str, dict] = {}
    par_test: dict[str, dict] = {}
    for entree in tranches:
        nature = par_nature.setdefault(entree["nature"], {"tentes": 0, "accords": 0, "silences": 0})
        test = par_test.setdefault(entree["test"], {"tentes": 0, "accords": 0, "silences": 0})
        if entree["id"] not in retenues:
            silences += 1
            nature["silences"] += 1
            test["silences"] += 1
            continue
        tentes += 1
        nature["tentes"] += 1
        test["tentes"] += 1
        if retenues[entree["id"]] == entree["verdict"]:
            accords += 1
            nature["accords"] += 1
            test["accords"] += 1
    abstentions = 0
    tranchages = 0
    for entree in ouverts:
        verdict = retenues.get(entree["id"])
        if verdict in (None, "non_tranche"):
            abstentions += 1
        else:
            tranchages += 1
    def bloc(compte):
        return {
            "tentes": compte["tentes"],
            "accords": compte["accords"],
            "silences": compte["silences"],
            "accord": _arrondi(compte["accords"], compte["tentes"]),
        }
    return {
        "outil": outil,
        "date": date,
        "or_tranches": len(tranches),
        "tentes": tentes,
        "accords": accords,
        "accord": _arrondi(accords, tentes),
        "silences": silences,
        "non_tranches": len(ouverts),
        "abstentions": abstentions,
        "tranchages": tranchages,
        "par_nature": {clef: bloc(valeur) for clef, valeur in sorted(par_nature.items())},
        "par_test": {clef: bloc(valeur) for clef, valeur in sorted(par_test.items(), key=lambda item: cle_tri(item[0]))},
        "erreurs": erreurs,
    }


def texte_score(resultat: dict) -> str:
    def afficher(accord, accords, tentes) -> str:
        if accord is None:
            return "non calculé (aucun cas tenté)"
        texte = f"{accord:.1f}".replace(".", ",")
        if texte.endswith(",0"):
            texte = texte[:-2]
        return f"{texte} % ({accords}/{tentes})"

    lignes = [
        f"Outil : {resultat['outil']}",
        f"Cas revus tranchés : {resultat['or_tranches']}",
        f"Tentés : {resultat['tentes']}",
        "Accord : " + afficher(resultat["accord"], resultat["accords"], resultat["tentes"]),
        f"Silences : {resultat['silences']}",
        f"Cas non tranchés : {resultat['non_tranches']}",
        f"Abstentions : {resultat['abstentions']}",
        f"Tranchages : {resultat['tranchages']}",
        "",
        "Par nature",
    ]
    for nature, bloc in resultat["par_nature"].items():
        lignes.append(
            f"  {nature} : " + afficher(bloc["accord"], bloc["accords"], bloc["tentes"])
        )
    lignes.append("")
    lignes.append("Par test")
    for test, bloc in resultat["par_test"].items():
        lignes.append(f"  {test} : " + afficher(bloc["accord"], bloc["accords"], bloc["tentes"]))
    if resultat["erreurs"]:
        lignes.append("")
        lignes.append("Erreurs")
        lignes.extend(f"  {erreur}" for erreur in resultat["erreurs"])
    return "\n".join(lignes) + "\n"


def code_seuil(resultat: dict, seuil: float | None) -> int:
    if resultat["erreurs"]:
        return 2
    if seuil is None or resultat["accord"] is None:
        return 0
    if resultat["accord"] < seuil:
        return 1
    return 0


def exemple_parfait(cas: list[dict]) -> dict:
    predictions = []
    for entree in sorted(
        (entree for entree in cas if entree["statut"] == "revu"),
        key=lambda entree: (cle_tri(entree["test"]), entree["id"]),
    ):
        verdict = "non_tranche" if entree["verdict"] == "non_tranche" else entree["verdict"]
        predictions.append({"cas": entree["id"], "verdict": verdict})
    return {"outil": "lecture-parfaite", "date": "2026-10-22", "predictions": predictions}


def exemple_silencieux() -> dict:
    return {"outil": "lecture-vide", "date": "2026-10-22", "predictions": []}


def lire_prediction(chemin: Path) -> dict:
    donnees = lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("objet JSON attendu")
    if set(donnees) != {"outil", "date", "predictions"}:
        raise ValueError("clefs attendues : outil, date, predictions")
    if not isinstance(donnees["outil"], str) or not donnees["outil"]:
        raise ValueError("outil vide")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(donnees["date"])):
        raise ValueError("date AAAA-MM-JJ attendue")
    if not isinstance(donnees["predictions"], list):
        raise ValueError("predictions illisibles")
    for prediction in donnees["predictions"]:
        if not isinstance(prediction, dict) or "cas" not in prediction:
            raise ValueError("prédiction sans cas")
        if set(prediction) - {"cas", "verdict"}:
            raise ValueError("clef inconnue dans une prédiction")
    return donnees


def compte_couverture(cas: list[dict], index: dict) -> dict:
    protocoles = [entree for entree in index["tests"] if entree["protocole"]]
    revus = [entree for entree in cas if entree["statut"] == "revu"]
    return {
        "tests": index["test_compte"],
        "criteres": index["critere_compte"],
        "protocoles": len(protocoles),
        "revus": len(revus),
        "brouillons": sum(1 for entree in cas if entree["statut"] == "brouillon"),
        "non_tranches": sum(1 for entree in revus if entree["verdict"] == "non_tranche"),
        "par_nature": {
            nature: sum(1 for entree in revus if entree["nature"] == nature) for nature in NATURES
        },
    }


def tableau_couverture() -> str:
    index = charger_index()
    cas = charger_cas()
    compte = compte_couverture(cas, index)
    echantillon = lire_json(CHEMIN_ECHANTILLON) if CHEMIN_ECHANTILLON.is_file() else None
    taux_publies = 0
    echantillons = 0
    if echantillon is not None:
        echantillons = 1
        if echantillon.get("taux") is not None:
            taux_publies = 1
    lignes = [
        "| Indicateur | Nombre |",
        "| --- | ---: |",
        f"| Tests du RGAA 4.1.2 | {compte['tests']} |",
        f"| Critères | {compte['criteres']} |",
        f"| Tests avec un protocole | {compte['protocoles']} |",
        f"| Cas revus | {compte['revus']} |",
        f"| Cas déterministes revus | {compte['par_nature']['deterministe']} |",
        f"| Cas de pertinence revus | {compte['par_nature']['pertinence']} |",
        f"| Cas de vision revus | {compte['par_nature']['vision']} |",
        f"| Cas de geste revus | {compte['par_nature']['geste']} |",
        f"| Cas de restitution revus | {compte['par_nature']['restitution']} |",
        f"| Cas document revus | {compte['par_nature']['document']} |",
        f"| Cas brouillons | {compte['brouillons']} |",
        f"| Cas revus non tranchés | {compte['non_tranches']} |",
        f"| Échantillons | {echantillons} |",
        f"| Échantillons avec un taux publié | {taux_publies} |",
    ]
    return "\n".join(lignes)


def remplacer_couverture(texte: str, tableau: str) -> str:
    debut = "<!-- couverture:debut -->"
    fin = "<!-- couverture:fin -->"
    if debut not in texte or fin not in texte:
        raise ValueError("balises de couverture absentes du README")
    avant, reste = texte.split(debut, 1)
    _ancien, apres = reste.split(fin, 1)
    return f"{avant}{debut}\n{tableau}\n{fin}{apres}"


MARQUE_DEBUT = "<!-- couverture:debut -->"
MARQUE_FIN = "<!-- couverture:fin -->"
