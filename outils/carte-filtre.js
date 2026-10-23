/* Filtre de la carte des tests. Préfixe sur le numéro, fragment sur l'intitulé. */
(function (root) {
  function filtrerTests(tests, requete) {
    var brut = String(requete || "").trim().toLowerCase();
    if (!brut) {
      return tests.map(function (test) {
        return test.id;
      });
    }
    var jetons = brut.split(/\s+/);
    return tests
      .filter(function (test) {
        var identifiant = test.id.toLowerCase();
        var intitule = test.intitule.toLowerCase();
        return jetons.every(function (jeton) {
          var prefixe = identifiant === jeton || identifiant.indexOf(jeton + ".") === 0;
          return prefixe || intitule.indexOf(jeton) !== -1;
        });
      })
      .map(function (test) {
        return test.id;
      });
  }

  function appliquer(racine, requete) {
    var articles = Array.prototype.slice.call(racine.querySelectorAll("[data-test]"));
    var tests = articles.map(function (article) {
      return {
        id: article.getAttribute("data-test"),
        intitule: article.getAttribute("data-intitule") || "",
      };
    });
    var gardes = {};
    filtrerTests(tests, requete).forEach(function (identifiant) {
      gardes[identifiant] = true;
    });
    var nombre = 0;
    articles.forEach(function (article) {
      var montrer = !!gardes[article.getAttribute("data-test")];
      article.hidden = !montrer;
      if (montrer) nombre += 1;
    });
    racine.querySelectorAll("[data-critere]").forEach(function (bloc) {
      var visible = bloc.querySelector("[data-test]:not([hidden])");
      bloc.hidden = !visible;
    });
    racine.querySelectorAll("[data-theme]").forEach(function (bloc) {
      var visible = bloc.querySelector("[data-critere]:not([hidden])");
      bloc.hidden = !visible;
    });
    return nombre;
  }

  var api = { filtrerTests: filtrerTests, appliquer: appliquer };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.CarteFiltre = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
