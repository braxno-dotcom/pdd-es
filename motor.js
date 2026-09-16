/* Движок теста. Один на все страницы: экзамен и тренировка по теме отличаются
   только настройками, которые страница кладёт в window.MODO.

   MODO = {tema: "velocidad"|null, examen: true|false}
   - examen: 30 вопросов вперемешку, больше 3 ошибок — не сдал (как в DGT);
   - тема: все вопросы темы, без порога, для тренировки.

   ⚠️ Варианты ответов перемешиваются: в банке правильный всегда первый,
   иначе его легко запомнить по месту, а не по правилу. */

(function () {
  var MODO = window.MODO || { tema: null, examen: false };
  var PREGUNTAS_EXAMEN = 30;
  var FALLOS_MAX = 3;

  var lista = [];
  var indice = 0;
  var aciertos = 0;
  var fallos = [];

  var $ = function (id) { return document.getElementById(id); };

  function mezclar(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function preparar() {
    var base = PREGUNTAS.filter(function (p) { return !MODO.tema || p.t === MODO.tema; });
    base = mezclar(base);
    if (MODO.examen) base = base.slice(0, PREGUNTAS_EXAMEN);
    lista = base.map(function (p) {
      // Перемешиваем варианты и запоминаем, куда уехал правильный.
      var pares = p.o.map(function (texto, i) { return { texto: texto, ok: i === p.a }; });
      pares = mezclar(pares);
      return { q: p.q, q_ru: p.q_ru, opciones: pares, t: p.t };
    });
    indice = 0; aciertos = 0; fallos = [];
  }

  function pintar() {
    var p = lista[indice];
    var total = lista.length;
    $("barra").style.width = Math.round((indice / total) * 100) + "%";
    $("contador").innerHTML = "Вопрос <b>" + (indice + 1) + "</b> из " + total;
    $("puntos").innerHTML = MODO.examen
      ? "Ошибок: <b>" + fallos.length + "</b> из " + FALLOS_MAX
      : "Верно: <b>" + aciertos + "</b>";

    var html = '<div class="pregunta-es">' + p.q + "</div>";
    html += '<div class="pregunta-ru">' + p.q_ru + "</div>";
    p.opciones.forEach(function (o, i) {
      html += '<button class="opcion" data-i="' + i + '">' + o.texto + "</button>";
    });
    $("zona").innerHTML = html;

    Array.prototype.forEach.call($("zona").querySelectorAll(".opcion"), function (b) {
      b.addEventListener("click", function () { responder(parseInt(b.dataset.i, 10)); });
    });
  }

  function responder(i) {
    var p = lista[indice];
    var botones = $("zona").querySelectorAll(".opcion");
    var bien = p.opciones[i].ok;

    Array.prototype.forEach.call(botones, function (b, j) {
      b.disabled = true;
      if (p.opciones[j].ok) b.classList.add("bien");
      else if (j === i) b.classList.add("mal");
    });

    if (bien) {
      aciertos++;
    } else {
      var correcta = p.opciones.filter(function (o) { return o.ok; })[0].texto;
      fallos.push({ q: p.q, q_ru: p.q_ru, correcta: correcta });
    }

    var aviso = document.createElement("div");
    aviso.className = "aviso " + (bien ? "bien" : "mal");
    aviso.innerHTML = bien
      ? "Верно"
      : "Правильный ответ: <b>" + p.opciones.filter(function (o) { return o.ok; })[0].texto + "</b>";
    $("zona").insertBefore(aviso, $("zona").firstChild);

    var siguiente = document.createElement("button");
    siguiente.className = "boton";
    siguiente.textContent = indice + 1 < lista.length ? "Дальше" : "Итог";
    siguiente.addEventListener("click", function () {
      indice++;
      if (indice >= lista.length || (MODO.examen && fallos.length > FALLOS_MAX)) terminar();
      else pintar();
    });
    $("zona").appendChild(siguiente);
  }

  function terminar() {
    $("barra").style.width = "100%";
    $("contador").textContent = "";
    $("puntos").textContent = "";

    var aprobado = MODO.examen ? fallos.length <= FALLOS_MAX : true;
    var html = '<div class="resultado">';
    html += '<div class="nota ' + (aprobado ? "aprobado" : "suspenso") + '">' + aciertos + " / " + lista.length + "</div>";

    if (MODO.examen) {
      html += aprobado
        ? "<p><b>Сдано.</b> На экзамене DGT допускается не больше трёх ошибок из тридцати — ты уложился.</p>"
        : "<p><b>Не сдано.</b> На экзамене DGT больше трёх ошибок из тридцати — это незачёт. Разбери ошибки и пройди ещё раз.</p>";
    } else {
      html += "<p>Тренировка по теме закончена.</p>";
    }

    if (fallos.length) {
      html += "<h3 style='margin-top:18px;text-align:left'>Разбор ошибок</h3>";
      fallos.forEach(function (f) {
        html += '<div class="fallo"><div class="es">' + f.q + '</div><div class="ru">' + f.q_ru + '</div>';
        html += '<div class="ok">Правильно: ' + f.correcta + "</div></div>";
      });
    }
    html += "</div>";
    $("zona").innerHTML = html;

    var otra = document.createElement("button");
    otra.className = "boton";
    otra.textContent = "Пройти ещё раз";
    otra.addEventListener("click", empezar);
    $("zona").appendChild(otra);

    var luci = document.createElement("a");
    luci.className = "boton secundario";
    luci.href = "https://repetiteur.onrender.com/?c=es-pdd";
    luci.textContent = "Спросить Люси, если что-то непонятно";
    $("zona").appendChild(luci);
  }

  function empezar() { preparar(); pintar(); }

  document.addEventListener("DOMContentLoaded", empezar);
})();
