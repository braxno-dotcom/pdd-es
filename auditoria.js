/* Проверка банка вопросов и перемешивания:  node auditoria.js

   Требования, которые тут меряются, а не объявляются:
   1. Перемешивание честное — правильный ответ попадает в каждую строку поровну.
      У французского сайта 12 сен 2026 нашли обратное: sort() со случайным
      сравнением давал 37,5 % на первую строку и 25 % на третью.
   2. Правильный ответ не выдаёт себя длиной. Классическая подсказка: самый
      длинный и подробный вариант — правильный. Если так, ученик сдаёт тест,
      не зная правил, а на экзамене проваливается.
   3. Нет вопросов, где ответ всегда «да»: у односложных пар надо и «нет».
   4. У каждого варианта есть перевод, иначе тест бесполезен для новичка.
*/
var PREGUNTAS = require("./preguntas.js");

function mezclar(a) {
  a = a.slice();
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}

var problemas = 0;
function mal(msg) { problemas++; console.log("  ⚠️ " + msg); }

console.log("1. Структура банка");
var temas = {};
PREGUNTAS.forEach(function (p, i) {
  temas[p.t] = (temas[p.t] || 0) + 1;
  if (p.a !== 0) mal("вопрос " + i + ": правильный не первый в банке");
  if (!p.o_ru || p.o_ru.length !== p.o.length) mal("вопрос " + i + ": нет перевода вариантов — " + p.q);
  if (!p.e) mal("вопрос " + i + ": нет объяснения — " + p.q);
  if (new Set(p.o).size !== p.o.length) mal("вопрос " + i + ": повторяющийся вариант");
  if (p.o.length < 3) mal("вопрос " + i + ": меньше трёх вариантов");
});
console.log("   вопросов: " + PREGUNTAS.length + ", тем: " + Object.keys(temas).length);
Object.keys(temas).forEach(function (t) { console.log("   " + t + ": " + temas[t]); });

console.log("\n2. Перемешивание: 100 000 прогонов на трёх вариантах");
var conteo = [0, 0, 0];
for (var n = 0; n < 100000; n++) {
  var p = PREGUNTAS[n % PREGUNTAS.length];
  if (p.o.length !== 3) continue;
  var pares = mezclar(p.o.map(function (o, i) { return { ok: i === p.a }; }));
  for (var k = 0; k < 3; k++) if (pares[k].ok) conteo[k]++;
}
var suma = conteo[0] + conteo[1] + conteo[2];
conteo.forEach(function (c, i) {
  var pct = (c / suma) * 100;
  console.log("   строка " + (i + 1) + ": " + pct.toFixed(1) + " %");
  if (Math.abs(pct - 33.33) > 1.5) mal("перекос в строке " + (i + 1) + ": " + pct.toFixed(1) + " %");
});

console.log("\n3. Не выдаёт ли себя правильный ответ длиной");
// ⚠️ Меряем ОТРЫВ, а не просто «длиннее всех». Правильный ответ на символ длиннее
// соседнего ничего не подсказывает; подсказывает развёрнутая фраза против двух
// коротких огрызков. Порог 1,2 подобран по тому, что видно глазом на телефоне.
var masLargo = 0, conVentaja = 0, peor = 1;
PREGUNTAS.forEach(function (p, i) {
  var largos = p.o.map(function (o) { return o.length; });
  var otros = largos.filter(function (_, j) { return j !== p.a; });
  var max = Math.max.apply(null, largos);
  var ventaja = largos[p.a] / Math.max.apply(null, otros);
  if (ventaja > peor) peor = ventaja;
  if (largos[p.a] === max && largos.filter(function (l) { return l === max; }).length === 1) masLargo++;
  if (ventaja >= 1.2) {
    conVentaja++;
    mal("вопрос " + i + ": правильный длиннее прочих в " + ventaja.toFixed(2) + " раза — " + p.o[p.a]);
  }
});
console.log("   правильный длиннее остальных хоть на символ: " + ((masLargo / PREGUNTAS.length) * 100).toFixed(0) + " % вопросов");
console.log("   с заметным отрывом (от 1,2 раза): " + conVentaja + ", самый большой отрыв x" + peor.toFixed(2));

console.log("\n4. Односложные пары да/нет");
var siNo = PREGUNTAS.filter(function (p) {
  return p.o.every(function (o) { return /^(s[ií]|no)\b/i.test(o); });
});
if (siNo.length) {
  var siCorrecto = siNo.filter(function (p) { return /^s[ií]/i.test(p.o[p.a]); }).length;
  console.log("   таких вопросов: " + siNo.length + ", из них ответ «да»: " + siCorrecto);
  if (siNo.length >= 4 && (siCorrecto === 0 || siCorrecto === siNo.length))
    mal("во всех парах да/нет ответ одинаковый — запоминается ответ, а не правило");
} else {
  console.log("   таких вопросов нет: везде три развёрнутых варианта");
}

console.log("\nИтог: " + (problemas ? problemas + " замечаний" : "замечаний нет"));
process.exit(problemas ? 1 : 0);
