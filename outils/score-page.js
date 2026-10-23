/* Port de banc.resultat_score et de banc._arrondi. Le Python reste la source. */
(function (root) {
  var VERDICTS = ["conforme", "non_conforme", "non_applicable", "non_tranche"];
  var TRANCHES = ["conforme", "non_conforme", "non_applicable"];

  function arrondi(part, total) {
    if (total === 0) return null;
    var numerateur = part * 1000;
    var quotient = Math.floor(numerateur / total);
    var reste = numerateur % total;
    if (reste * 2 >= total) quotient += 1;
    var entier = Math.floor(quotient / 10);
    var dixieme = quotient % 10;
    if (dixieme === 0) return entier;
    return Number(entier + "." + dixieme);
  }

  function cleTri(identifiant) {
    return identifiant.split(".").map(function (morceau) {
      return Number(morceau);
    });
  }

  function comparerTests(gauche, droite) {
    var a = cleTri(gauche);
    var b = cleTri(droite);
    var i;
    for (i = 0; i < a.length; i += 1) {
      if (a[i] !== b[i]) return a[i] - b[i];
    }
    return 0;
  }

  function noter(outil, date, predictions, grille) {
    var parId = {};
    var erreurs = [];
    var vues = {};
    var retenues = {};
    var i;
    grille.forEach(function (entree) {
      parId[entree.id] = entree;
    });
    predictions.forEach(function (prediction) {
      var identifiant = prediction.cas;
      if (Object.prototype.hasOwnProperty.call(vues, identifiant)) {
        erreurs.push("prédiction doublée : " + identifiant);
        return;
      }
      vues[identifiant] = true;
      if (!Object.prototype.hasOwnProperty.call(parId, identifiant)) {
        erreurs.push("cas inconnu : " + identifiant);
        return;
      }
      if (
        Object.prototype.hasOwnProperty.call(prediction, "verdict") &&
        VERDICTS.indexOf(prediction.verdict) < 0
      ) {
        erreurs.push("verdict inconnu pour " + identifiant);
        return;
      }
      retenues[identifiant] = Object.prototype.hasOwnProperty.call(prediction, "verdict")
        ? prediction.verdict
        : null;
    });
    var tranches = grille.filter(function (entree) {
      return entree.statut === "revu" && TRANCHES.indexOf(entree.verdict) >= 0;
    });
    var ouverts = grille.filter(function (entree) {
      return entree.statut === "revu" && entree.verdict === "non_tranche";
    });
    var accords = 0;
    var tentes = 0;
    var silences = 0;
    var parNature = {};
    var parTest = {};
    tranches.forEach(function (entree) {
      if (!parNature[entree.nature]) parNature[entree.nature] = { tentes: 0, accords: 0, silences: 0 };
      if (!parTest[entree.test]) parTest[entree.test] = { tentes: 0, accords: 0, silences: 0 };
      if (!Object.prototype.hasOwnProperty.call(retenues, entree.id)) {
        silences += 1;
        parNature[entree.nature].silences += 1;
        parTest[entree.test].silences += 1;
        return;
      }
      tentes += 1;
      parNature[entree.nature].tentes += 1;
      parTest[entree.test].tentes += 1;
      if (retenues[entree.id] === entree.verdict) {
        accords += 1;
        parNature[entree.nature].accords += 1;
        parTest[entree.test].accords += 1;
      }
    });
    var abstentions = 0;
    var tranchages = 0;
    ouverts.forEach(function (entree) {
      var verdict = Object.prototype.hasOwnProperty.call(retenues, entree.id)
        ? retenues[entree.id]
        : null;
      if (verdict === null || verdict === "non_tranche") abstentions += 1;
      else tranchages += 1;
    });
    function bloc(compte) {
      return {
        tentes: compte.tentes,
        accords: compte.accords,
        silences: compte.silences,
        accord: arrondi(compte.accords, compte.tentes),
      };
    }
    var natures = {};
    Object.keys(parNature)
      .sort()
      .forEach(function (clef) {
        natures[clef] = bloc(parNature[clef]);
      });
    var tests = {};
    Object.keys(parTest)
      .sort(comparerTests)
      .forEach(function (clef) {
        tests[clef] = bloc(parTest[clef]);
      });
    return {
      outil: outil,
      date: date,
      or_tranches: tranches.length,
      tentes: tentes,
      accords: accords,
      accord: arrondi(accords, tentes),
      silences: silences,
      non_tranches: ouverts.length,
      abstentions: abstentions,
      tranchages: tranchages,
      par_nature: natures,
      par_test: tests,
      erreurs: erreurs,
    };
  }

  function egal(gauche, droite) {
    var i;
    if (gauche === droite) return true;
    if (gauche === null || droite === null) return false;
    if (typeof gauche !== "object" || typeof droite !== "object") return false;
    if (Array.isArray(gauche)) {
      if (!Array.isArray(droite) || gauche.length !== droite.length) return false;
      for (i = 0; i < gauche.length; i += 1) {
        if (!egal(gauche[i], droite[i])) return false;
      }
      return true;
    }
    var clefsG = Object.keys(gauche).sort();
    var clefsD = Object.keys(droite).sort();
    if (clefsG.length !== clefsD.length) return false;
    for (i = 0; i < clefsG.length; i += 1) {
      if (clefsG[i] !== clefsD[i] || !egal(gauche[clefsG[i]], droite[clefsD[i]])) return false;
    }
    return true;
  }

  function jeuxConformes(oracle) {
    var noms = Object.keys(oracle.jeux);
    var i;
    for (i = 0; i < noms.length; i += 1) {
      var jeu = oracle.jeux[noms[i]];
      var obtenu = noter(
        jeu.prediction.outil,
        jeu.prediction.date,
        jeu.prediction.predictions,
        oracle.grille
      );
      if (!egal(obtenu, jeu.resultat)) return noms[i];
    }
    return "";
  }

  function lirePrediction(donnees) {
    if (!donnees || typeof donnees !== "object" || Array.isArray(donnees)) {
      return "objet JSON attendu";
    }
    var clefs = Object.keys(donnees).sort();
    if (clefs.join(",") !== "date,outil,predictions") return "clefs attendues : outil, date, predictions";
    if (typeof donnees.outil !== "string" || !donnees.outil) return "outil vide";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(donnees.date)) return "date AAAA-MM-JJ attendue";
    if (!Array.isArray(donnees.predictions)) return "predictions illisibles";
    var i;
    for (i = 0; i < donnees.predictions.length; i += 1) {
      var prediction = donnees.predictions[i];
      if (!prediction || typeof prediction !== "object" || !Object.prototype.hasOwnProperty.call(prediction, "cas")) {
        return "prédiction sans cas";
      }
      var inconnues = Object.keys(prediction).filter(function (clef) {
        return clef !== "cas" && clef !== "verdict";
      });
      if (inconnues.length) return "clef inconnue dans une prédiction";
    }
    return "";
  }

  function afficherAccord(accord, accords, tentes) {
    if (accord === null) return "non calculé (aucun cas tenté)";
    var texte = accord.toFixed(1).replace(".", ",");
    if (texte.slice(-2) === ",0") texte = texte.slice(0, -2);
    return texte + " % (" + accords + "/" + tentes + ")";
  }

  function htmlResultat(resultat, grille) {
    var brouillons = grille.filter(function (entree) {
      return entree.statut === "brouillon";
    }).length;
    var lignes = [
      "Outil : " + resultat.outil,
      "Cas revus tranchés : " + resultat.or_tranches,
      "Cas revus non tranchés : " + resultat.non_tranches,
      "Brouillons hors accord : " + brouillons,
      "Tentés : " + resultat.tentes,
      "Accord : " + afficherAccord(resultat.accord, resultat.accords, resultat.tentes),
      "Silences : " + resultat.silences,
      "Abstentions : " + resultat.abstentions,
      "Tranchages : " + resultat.tranchages,
    ];
    var natures = Object.keys(resultat.par_nature);
    if (natures.length) {
      lignes.push("Par nature");
      natures.forEach(function (nature) {
        var bloc = resultat.par_nature[nature];
        lignes.push(
          nature + " : " + afficherAccord(bloc.accord, bloc.accords, bloc.tentes)
        );
      });
    }
    if (resultat.erreurs.length) {
      lignes.push("Erreurs");
      resultat.erreurs.forEach(function (erreur) {
        lignes.push(erreur);
      });
    }
    return lignes.join("\n");
  }

  function demarrer() {
    var balise = document.getElementById("oracle-score");
    var forme = document.getElementById("forme-prediction");
    var zone = document.getElementById("resultat-score");
    if (!balise || !forme || !zone) return;
    var oracle = null;
    var blocage = "";
    try {
      oracle = JSON.parse(balise.textContent);
    } catch (exc) {
      blocage = "L’oracle de la page est illisible. Aucun accord n’est affiché.";
    }
    if (!blocage) {
      var ecart = jeuxConformes(oracle);
      if (ecart) {
        blocage =
          "Le calcul de la page ne reproduit pas le scoreur (" +
          ecart +
          "). Aucun accord n’est affiché.";
      }
    }
    if (blocage) zone.textContent = blocage;
    var champ = document.getElementById("prediction");
    var fichier = document.getElementById("fichier-prediction");
    if (fichier) {
      fichier.addEventListener("change", function () {
        var choisi = fichier.files && fichier.files[0];
        if (!choisi) return;
        var lecteur = new FileReader();
        lecteur.onload = function () {
          champ.value = String(lecteur.result || "");
        };
        lecteur.readAsText(choisi);
      });
    }
    forme.addEventListener("submit", function (event) {
      event.preventDefault();
      if (blocage) {
        zone.textContent = blocage;
        return;
      }
      var donnees;
      try {
        donnees = JSON.parse(champ.value);
      } catch (exc) {
        zone.textContent = "Ce texte n’est pas du JSON.";
        return;
      }
      var message = lirePrediction(donnees);
      if (message) {
        zone.textContent = message;
        return;
      }
      var resultat = noter(donnees.outil, donnees.date, donnees.predictions, oracle.grille);
      zone.textContent = htmlResultat(resultat, oracle.grille);
    });
    document.documentElement.classList.add("js");
  }

  var api = {
    arrondi: arrondi,
    noter: noter,
    jeuxConformes: jeuxConformes,
    lirePrediction: lirePrediction,
    htmlResultat: htmlResultat,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ScorePage = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", demarrer);
    else demarrer();
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
