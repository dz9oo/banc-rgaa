const test = require("node:test");
const assert = require("node:assert/strict");
const { filtrerTests } = require("./carte-filtre.js");

const tests = [
  { id: "1.1.1", intitule: "Chaque image porteuse d’information a-t-elle une alternative ?" },
  { id: "8.1.1", intitule: "Le type de document (balise doctype) est-il présent ?" },
  { id: "8.1.2", intitule: "Le type de document est-il valide ?" },
  { id: "8.10.1", intitule: "Autre critère" },
  { id: "10.7.1", intitule: "La prise de focus est-elle visible ?" },
];

test("un numéro filtre par préfixe", () => {
  assert.deepEqual(filtrerTests(tests, "8.1"), ["8.1.1", "8.1.2"]);
});

test("un mot filtre l'intitulé", () => {
  assert.deepEqual(filtrerTests(tests, "doctype"), ["8.1.1"]);
  assert.deepEqual(filtrerTests(tests, "focus"), ["10.7.1"]);
});

test("une requête vide garde tous les tests", () => {
  assert.equal(filtrerTests(tests, "  ").length, tests.length);
});
