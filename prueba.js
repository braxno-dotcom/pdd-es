/* Прогон движка без браузера:  node prueba.js

   ⚠️ Зачем: страницы отдаются GitHub Pages, и «открылось» ещё не значит «работает».
   Тут подставляется простейший DOM и проверяется то, что видит человек: появился ли
   вопрос, есть ли перевод у каждого варианта, засчитался ли правильный ответ,
   показалось ли объяснение, переключается ли кнопка перевода. */

var fs = require("fs");
var vm = require("vm");

function nodo(tag) {
  var n = {
    tag: tag || "div",
    _html: "",
    hijos: [],
    clases: {},
    dataset: {},
    style: {},
    textContent: "",
    disabled: false,
    manejadores: {},
    classList: {
      add: function (c) { n.clases[c] = true; },
      remove: function (c) { delete n.clases[c]; },
      toggle: function (c, v) { if (v === undefined) v = !n.clases[c]; if (v) n.clases[c] = true; else delete n.clases[c]; },
      contains: function (c) { return !!n.clases[c]; }
    },
    addEventListener: function (ev, fn) { n.manejadores[ev] = fn; },
    appendChild: function (h) { n.hijos.push(h); return h; },
    insertBefore: function (h) { n.hijos.unshift(h); return h; },
    querySelectorAll: function (sel) { return n._botones(sel); },
    _botones: function (sel) {
      // Разбираем только то, что нужно движку: список кнопок-вариантов.
      // ⚠️ Кэш обязателен: движок вешает обработчик на СВОЙ результат вызова,
      // и без кэша тест кликал бы по другим объектам, чем те, что слушают.
      if (sel !== ".opcion") return [];
      if (n._cacheHtml === n._html) return n._cacheBotones;
      var res = [];
      var re = /<button class="opcion" data-i="(\d+)">([\s\S]*?)<\/button>/g, m;
      while ((m = re.exec(n._html))) {
        (function (i, cuerpo) {
          var b = nodo("button");
          b.dataset.i = String(i);
          b.cuerpo = cuerpo;
          res.push(b);
        })(m[1], m[2]);
      }
      n._cacheHtml = n._html;
      n._cacheBotones = res;
      return res;
    }
  };
  Object.defineProperty(n, "innerHTML", {
    get: function () { return n._html; },
    set: function (v) { n._html = v; n.hijos = []; }
  });
  Object.defineProperty(n, "firstChild", { get: function () { return n.hijos[0] || null; } });
  return n;
}

var elementos = { zona: nodo(), barra: nodo(), contador: nodo(), puntos: nodo(), traducir: null };
var cuerpo = nodo("body");

var sandbox = {
  console: console,
  localStorage: (function () {
    var d = {};
    return { getItem: function (k) { return k in d ? d[k] : null; }, setItem: function (k, v) { d[k] = String(v); } };
  })(),
  document: {
    body: cuerpo,
    getElementById: function (id) { return elementos[id] || null; },
    createElement: function (t) { return nodo(t); },
    addEventListener: function (ev, fn) { sandbox.__cargado = fn; }
  },
  window: {}
};
sandbox.window.MODO = { tema: null, examen: true };
sandbox.global = sandbox;

vm.createContext(sandbox);
vm.runInContext(fs.readFileSync("preguntas-auto.js", "utf8").replace(/if \(typeof module[\s\S]*$/, ""), sandbox);
vm.runInContext(fs.readFileSync("preguntas.js", "utf8").replace(/if \(typeof module[\s\S]*$/, ""), sandbox);
vm.runInContext(fs.readFileSync("senales.js", "utf8").replace(/if \(typeof module[\s\S]*$/, ""), sandbox);
vm.runInContext(fs.readFileSync("motor.js", "utf8"), sandbox);

var fallos = 0;
function comprobar(nombre, ok, detalle) {
  console.log((ok ? "  ок    " : "  ПЛОХО ") + nombre + (detalle && !ok ? " → " + detalle : ""));
  if (!ok) fallos++;
}

sandbox.__cargado();   // DOMContentLoaded

console.log("Прогон экзамена (30 вопросов, 3 ошибки)");
comprobar("вопрос нарисован", /class="pregunta-es"/.test(elementos.zona.innerHTML));
comprobar("перевод вопроса на месте", /class="pregunta-ru"/.test(elementos.zona.innerHTML));
var botones = elementos.zona.querySelectorAll(".opcion");
comprobar("вариантов не меньше трёх", botones.length >= 3, "их " + botones.length);
var conRu = botones.filter(function (b) { return /<span class="ru">/.test(b.cuerpo); });
comprobar("у каждого варианта есть перевод", conRu.length === botones.length,
          conRu.length + " из " + botones.length);
comprobar("счётчик показывает 1 из 30", /из 30/.test(elementos.contador.innerHTML));

// Кнопка перевода: испанский первым, перевод по кнопке и только на один вопрос.
var boton = cuerpo.hijos.filter(function (h) { return h.tag === "button"; })[0];
comprobar("кнопка перевода добавлена", !!boton);
comprobar("вопрос приходит по-испански", cuerpo.classList.contains("sin-ru"));
comprobar("на кнопке написано «Перевести вопрос»", /Перевести/.test(boton ? boton.textContent : ""));
if (boton) {
  boton.manejadores.click();
  comprobar("нажатие открывает перевод", !cuerpo.classList.contains("sin-ru"));
  comprobar("на кнопке написано «Скрыть перевод»", /Скрыть/.test(boton.textContent));
  boton.manejadores.click();
  comprobar("повторное нажатие прячет обратно", cuerpo.classList.contains("sin-ru"));
}

// Отвечаем правильно: движок держит правильный за текст варианта.
var textoPregunta = (elementos.zona.innerHTML.match(/class="pregunta-es">([^<]+)</) || [])[1];
var original = null;
vm.runInContext("__P = PREGUNTAS;", sandbox);
sandbox.__P.forEach(function (p) { if (p.q === textoPregunta) original = p; });
comprobar("вопрос найден в банке", !!original, textoPregunta);

if (original) {
  var correcto = original.o[original.a];
  var indice = -1;
  botones.forEach(function (b, i) { if (b.cuerpo.indexOf(correcto) !== -1) indice = i; });
  comprobar("правильный вариант есть среди показанных", indice !== -1, correcto);
  if (indice !== -1) {
    botones[indice].manejadores.click();
    // Движок вставляет отклик отдельным узлом (insertBefore), а не в innerHTML —
    // в браузере он виден, в заглушке лежит среди детей.
    var respuesta = elementos.zona.hijos.map(function (h) { return h.innerHTML || h.textContent || ""; }).join(" ");
    comprobar("ответ засчитан верным", /Верно/.test(respuesta), respuesta.slice(0, 60));
    comprobar("объяснение показано", respuesta.indexOf(original.e.slice(0, 20)) !== -1, original.e.slice(0, 30));
    comprobar("после ответа язык остался как выбрал человек", cuerpo.classList.contains("sin-ru"));
    comprobar("кнопка перевода на месте", boton.style.display !== "none");
    comprobar("ошибок по-прежнему ноль", /Ошибок: <b>0<\/b>/.test(elementos.puntos.innerHTML));

    // ⚠️ Главное: следующий вопрос снова приходит по-испански.
    var siguiente = elementos.zona.hijos.filter(function (h) { return h.textContent === "Дальше"; })[0];
    comprobar("кнопка «Дальше» появилась", !!siguiente);
    if (siguiente) {
      siguiente.manejadores.click();
      comprobar("следующий вопрос по-испански, раз перевод выключен", cuerpo.classList.contains("sin-ru"));
      comprobar("кнопка перевода на месте", boton.style.display !== "none");
      // ⚠️ Главное отличие от первой версии: включённый перевод ДЕРЖИТСЯ дальше,
      // как на французском сайте. Иначе человек жмёт кнопку тридцать раз подряд.
      boton.manejadores.click();
      comprobar("перевод включён", !cuerpo.classList.contains("sin-ru"));
      var bs = elementos.zona.querySelectorAll(".opcion");
      bs[0].manejadores.click();
      var sig = elementos.zona.hijos.filter(function (h) { return h.textContent === "Дальше"; })[0];
      if (sig) {
        sig.manejadores.click();
        comprobar("на следующем вопросе перевод остался включён", !cuerpo.classList.contains("sin-ru"));
      }
      comprobar("у вариантов есть буквы A/B/C", /class="letra">A</.test(elementos.zona.innerHTML));
      comprobar("перевод стоит в скобках рядом", /class="ru">\(/.test(elementos.zona.innerHTML));
      comprobar("счётчик двигается вперёд", /Вопрос <b>[234]<\/b>/.test(elementos.contador.innerHTML), elementos.contador.innerHTML);
    }
  }
}


// Вопрос со знаком: картинка должна появиться над текстом.
console.log("\n" + 'Знак картинкой');
vm.runInContext('__P = PREGUNTAS;', sandbox);
var conSena = sandbox.__P.filter(function (p) { return p.s; });
comprobar('в банке есть вопросы со знаком', conSena.length > 0, 'их ' + conSena.length);
var dibujados = 0, intentos = 0;
while (dibujados === 0 && intentos < 80) {
  intentos++;
  sandbox.__cargado();
  if (/<svg /.test(elementos.zona.innerHTML)) dibujados++;
}
comprobar('знак отрисован над вопросом', dibujados > 0, 'не попался за ' + intentos + ' прогонов');

console.log(fallos ? "\nПровалено проверок: " + fallos : "\nВсе проверки пройдены");
process.exit(fallos ? 1 : 0);
