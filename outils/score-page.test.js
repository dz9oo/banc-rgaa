const test = require("node:test");
const assert = require("node:assert/strict");
const { noter, jeuxConformes, arrondi } = require("./score-page.js");
const oracle = require("../exemples/oracle-score.json");

test("les jeux de l'oracle reproduisent le scoreur", () => {
  assert.equal(jeuxConformes(oracle), "");
});

test("un brouillon connu ne change pas l'accord d'une lecture vide", () => {
  const vide = oracle.jeux.silencieuse.resultat;
  const brouillon = oracle.jeux.brouillon.resultat;
  assert.equal(brouillon.accord, vide.accord);
  assert.equal(brouillon.tentes, vide.tentes);
  assert.equal(brouillon.accords, vide.accords);
  assert.equal(brouillon.erreurs.length, 0);
});

test("l'arrondi moitié vers le haut retombe sur un dixième", () => {
  assert.equal(arrondi(0, 0), null);
  assert.equal(arrondi(1, 1), 100);
  assert.equal(arrondi(1, 3), 33.3);
  assert.equal(arrondi(2, 3), 66.7);
  assert.equal(arrondi(1, 8), 12.5);
});

test("noter ignore un brouillon et signale un cas inconnu", () => {
  const resultat = noter(
    "essai",
    "2026-10-22",
    [
      { cas: "4.13.1/lecteur-audio", verdict: "conforme" },
      { cas: "0.0.0/absent", verdict: "conforme" },
    ],
    oracle.grille
  );
  assert.equal(resultat.accord, null);
  assert.deepEqual(resultat.erreurs, ["cas inconnu : 0.0.0/absent"]);
});
