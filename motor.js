/* Движок теста. Один на все страницы: экзамен и тренировка по теме отличаются
   только настройками, которые страница кладёт в window.MODO.

   MODO = {tema: "velocidad"|null, examen: true|false}
   - examen: 30 вопросов вперемешку, больше 3 ошибок — не сдал (как в DGT);
   - тема: все вопросы темы, без порога, для тренировки.

   ⚠️ ЧЕСТНОЕ ПЕРЕМЕШИВАНИЕ (Фишер-Йетс), а не sort() со случайным сравнением.
   На французском сайте это померили 12 сен 2026: при трёх вариантах через sort()
   правильный попадал в первую строку в 37,5 % случаев, а в третью лишь в 25 %.
   Рука ученика привыкает не смотреть вниз, а на экзамене такого подарка нет.
   ⚠️ Меняется ТОЛЬКО порядок: правильный держится за текст варианта, а не за номер.
   Проверяется скриптом `auditoria.js` — он же меряет распределение на 100 000 прогонов.

   ⚠️⚠️ ПЕРЕВОД — СНАЧАЛА ИСПАНСКИЙ, ПЕРЕВОД ПО ЗАПРОСУ, И НА ОДИН ВОПРОС.
   Первая версия показывала русский всегда и помнила выбор — это было неправильно:
   человек читает перевод и испанскую строку не видит вовсе, а на экзамене её не будет.
   Теперь вопрос приходит по-испански; кнопка открывает перевод ТОЛЬКО текущего
   вопроса; следующий снова приходит по-испански. Сначала пробуешь понять сам —
   и только если не вышло, подглядываешь. Перевод правильного ответа после ответа
   показывается всегда: там уже не проверка, а объяснение. */

(function () {
  var MODO = window.MODO || { tema: null, examen: false };
  var PREGUNTAS_EXAMEN = 30;
  var FALLOS_MAX = 3;

  var lista = [];
  var indice = 0;
  var aciertos = 0;
  var fallos = [];
  var conRuso = false;   // состояние ОДНОГО вопроса, сбрасывается в pintar()
  var boton = null;      // кнопка перевода; держим ссылкой, а не поиском по id

  var $ = function (id) { return document.getElementById(id); };

  // Знак рисуется кодом из senales.js. ⚠️ Если файла нет (старый кеш браузера),
  // вопрос всё равно показывается — просто без картинки, а не падает молча.
  function dibujoSenal(codigo, pequeno) {
    if (!codigo || typeof SENALES === "undefined" || !SENALES[codigo]) return "";
    return '<div class="senal' + (pequeno ? " senal-min" : "") + '">' + SENALES[codigo] + "</div>";
  }

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
      // Перемешиваем варианты вместе с их переводами и запоминаем, куда уехал правильный.
      var pares = p.o.map(function (texto, i) {
        return { texto: texto, ru: (p.o_ru || [])[i] || "", ok: i === p.a };
      });
      pares = mezclar(pares);
      return { q: p.q, q_ru: p.q_ru, e: p.e || "", s: p.s || "", opciones: pares, t: p.t };
    });
    indice = 0; aciertos = 0; fallos = [];
  }

  function pintar() {
    conRuso = false;          // каждый новый вопрос приходит по-испански
    aplicarRuso();
    mostrarBoton(true);

    var p = lista[indice];
    var total = lista.length;
    $("barra").style.width = Math.round((indice / total) * 100) + "%";
    $("contador").innerHTML = "Вопрос <b>" + (indice + 1) + "</b> из " + total;
    $("puntos").innerHTML = MODO.examen
      ? "Ошибок: <b>" + fallos.length + "</b> из " + FALLOS_MAX
      : "Верно: <b>" + aciertos + "</b>";

    var html = dibujoSenal(p.s);
    html += '<div class="pregunta-es">' + p.q + "</div>";
    html += '<div class="pregunta-ru">' + p.q_ru + "</div>";
    p.opciones.forEach(function (o, i) {
      html += '<button class="opcion" data-i="' + i + '"><span class="es">' + o.texto + "</span>";
      if (o.ru) html += '<span class="ru">' + o.ru + "</span>";
      html += "</button>";
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
    var correcta = p.opciones.filter(function (o) { return o.ok; })[0];

    Array.prototype.forEach.call(botones, function (b, j) {
      b.disabled = true;
      if (p.opciones[j].ok) b.classList.add("bien");
      else if (j === i) b.classList.add("mal");
    });

    if (bien) aciertos++;
    else fallos.push({ q: p.q, q_ru: p.q_ru, s: p.s, correcta: correcta.texto, correcta_ru: correcta.ru, e: p.e });

    // Ответ дан — проверка кончилась, дальше объяснение. Русский тут виден всегда,
    // независимо от кнопки: прятать разбор бессмысленно.
    var aviso = document.createElement("div");
    aviso.className = "aviso " + (bien ? "bien" : "mal");
    aviso.innerHTML = (bien ? "<b>Верно.</b> " : "<b>Правильный ответ:</b> " + correcta.texto +
      (correcta.ru ? " — " + correcta.ru : "") + ". ") + (p.e ? p.e : "");
    $("zona").insertBefore(aviso, $("zona").firstChild);

    // Перевод вопроса после ответа тоже открываем: человек уже не угадывает.
    conRuso = true;
    aplicarRuso();
    mostrarBoton(false);

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
    mostrarBoton(false);
    conRuso = true;
    aplicarRuso();

    $("barra").style.width = "100%";
    $("contador").textContent = "";
    $("puntos").textContent = "";

    var aprobado = MODO.examen ? fallos.length <= FALLOS_MAX : true;
    var html = '<div class="resultado">';
    html += '<div class="nota ' + (aprobado ? "aprobado" : "suspenso") + '">' + aciertos + " / " + lista.length + "</div>";

    if (MODO.examen) {
      html += aprobado
        ? "<p><b>Сдано.</b> На экзамене DGT допускается не больше трёх ошибок из тридцати — ты уложился.</p>"
        : "<p><b>Не сдано.</b> Больше трёх ошибок из тридцати на экзамене DGT — это незачёт. Разбери ошибки и пройди ещё раз.</p>";
    } else {
      html += "<p>Тренировка по теме закончена.</p>";
    }

    if (fallos.length) {
      html += "<h3 style='margin-top:18px;text-align:left'>Разбор ошибок</h3>";
      fallos.forEach(function (f) {
        html += '<div class="fallo">' + dibujoSenal(f.s, true) + '<div class="es">' + f.q + '</div><div class="ru">' + f.q_ru + "</div>";
        html += '<div class="ok">Правильно: ' + f.correcta + (f.correcta_ru ? " — " + f.correcta_ru : "") + "</div>";
        if (f.e) html += '<div class="por">' + f.e + "</div>";
        html += "</div>";
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

  function aplicarRuso() {
    document.body.classList.toggle("sin-ru", !conRuso);
    if (boton) boton.textContent = conRuso ? "🇪🇸 Скрыть перевод" : "🇷🇺 Перевести вопрос";
  }

  function mostrarBoton(visible) {
    if (boton) boton.style.display = visible ? "" : "none";
  }

  function montarBoton() {
    boton = document.createElement("button");
    boton.id = "traducir";
    boton.className = "traducir";
    boton.addEventListener("click", function () {
      conRuso = !conRuso;
      aplicarRuso();
    });
    document.body.appendChild(boton);
    aplicarRuso();
  }

  function empezar() { preparar(); pintar(); }

  document.addEventListener("DOMContentLoaded", function () {
    montarBoton();
    empezar();
  });
})();
