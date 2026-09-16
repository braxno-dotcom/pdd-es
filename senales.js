/* Дорожные знаки — рисунком в коде, а не картинками.

   ⚠️ Почему нарисованы, а не взяты готовыми: у французского сайта знаков нет вовсе
   (там эмодзи), а тянуть чужие файлы — это чужая лицензия ради полукилобайта.
   Знак же — чистая геометрия: восьмиугольник, перевёрнутый треугольник, круг
   с каймой. Испанские знаки идут по Венской конвенции, формы международные.

   ⚠️ Всё в одном viewBox 100×100, поэтому любой знак ставится в любое место
   и остаётся чётким на любом экране. Цвета — по испанскому стандарту:
   красный AA151B у запретов, синий 1A56DB у предписаний, жёлтый F1BF00
   у приоритета.

   Ключ — код знака; в вопросе он пишется в поле `s`. */

const ROJO = "#c1121f", AZUL = "#1a56db", AMARILLO = "#f1bf00", NEGRO = "#1f2937";

function envolver(interior) {
  return '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img">' + interior + "</svg>";
}

// Заготовки форм, чтобы не повторять одно и то же двадцать раз.
const circuloProhibicion =
  '<circle cx="50" cy="50" r="44" fill="#fff" stroke="' + ROJO + '" stroke-width="9"/>';
const circuloAzul = '<circle cx="50" cy="50" r="46" fill="' + AZUL + '"/>';
const trianguloPeligro =
  '<polygon points="50,8 93,86 7,86" fill="#fff" stroke="' + ROJO + '" stroke-width="8" stroke-linejoin="round"/>';
const cuadradoAzul = '<rect x="6" y="6" width="88" height="88" rx="6" fill="' + AZUL + '"/>';

// Человечек и велосипед — упрощённые силуэты: на знаке они и есть силуэты.
function peaton(x, y, escala, color) {
  const c = color || NEGRO;
  return (
    '<g transform="translate(' + x + ',' + y + ') scale(' + escala + ')" fill="' + c + '">' +
    '<circle cx="0" cy="-16" r="5"/>' +
    '<path d="M0 -11 L0 2 M0 -8 L-7 -1 M0 -8 L7 -2 M0 2 L-6 14 M0 2 L7 13" stroke="' + c +
    '" stroke-width="3.4" fill="none" stroke-linecap="round"/></g>'
  );
}

function bicicleta(x, y, escala, color) {
  const c = color || NEGRO;
  return (
    '<g transform="translate(' + x + ',' + y + ') scale(' + escala + ')" fill="none" stroke="' + c +
    '" stroke-width="3">' +
    '<circle cx="-13" cy="6" r="9"/><circle cx="13" cy="6" r="9"/>' +
    '<path d="M-13 6 L-3 -8 L9 -8 L13 6 M-3 -8 L3 6 M9 -8 L13 -11" stroke-linecap="round"/>' +
    "</g>"
  );
}

const SENALES = {
  // ---------- ЗАПРЕТЫ ----------
  stop: envolver(
    '<polygon points="30,4 70,4 96,30 96,70 70,96 30,96 4,70 4,30" fill="' + ROJO + '" stroke="#fff" stroke-width="5"/>' +
    '<text x="50" y="61" text-anchor="middle" font-size="25" font-weight="bold" fill="#fff" font-family="Arial, sans-serif">STOP</text>'),

  ceda_el_paso: envolver(
    '<polygon points="50,93 5,15 95,15" fill="#fff" stroke="' + ROJO + '" stroke-width="9" stroke-linejoin="round"/>'),

  circulacion_prohibida: envolver(circuloProhibicion),

  entrada_prohibida: envolver(
    '<circle cx="50" cy="50" r="46" fill="' + ROJO + '"/>' +
    '<rect x="20" y="42" width="60" height="16" rx="2" fill="#fff"/>'),

  velocidad_maxima: envolver(
    circuloProhibicion +
    '<text x="50" y="64" text-anchor="middle" font-size="40" font-weight="bold" fill="' + NEGRO + '" font-family="Arial, sans-serif">50</text>'),

  velocidad_minima: envolver(
    circuloAzul +
    '<text x="50" y="64" text-anchor="middle" font-size="40" font-weight="bold" fill="#fff" font-family="Arial, sans-serif">60</text>'),

  prohibido_adelantar: envolver(
    circuloProhibicion +
    '<g transform="translate(0,4)">' +
    '<rect x="16" y="48" width="30" height="15" rx="3" fill="' + ROJO + '"/>' +
    '<rect x="21" y="41" width="17" height="8" rx="2" fill="' + ROJO + '"/>' +
    '<circle cx="24" cy="66" r="4.5" fill="' + NEGRO + '"/><circle cx="39" cy="66" r="4.5" fill="' + NEGRO + '"/>' +
    '<rect x="54" y="48" width="30" height="15" rx="3" fill="' + NEGRO + '"/>' +
    '<rect x="59" y="41" width="17" height="8" rx="2" fill="' + NEGRO + '"/>' +
    '<circle cx="62" cy="66" r="4.5" fill="' + NEGRO + '"/><circle cx="77" cy="66" r="4.5" fill="' + NEGRO + '"/>' +
    "</g>"),

  prohibido_camiones: envolver(
    circuloProhibicion +
    '<g transform="translate(0,3)">' +
    '<rect x="18" y="44" width="34" height="20" rx="2" fill="' + NEGRO + '"/>' +
    '<path d="M54 52 H70 L80 62 V64 H54 Z" fill="' + NEGRO + '"/>' +
    '<circle cx="30" cy="68" r="5" fill="' + NEGRO + '"/><circle cx="70" cy="68" r="5" fill="' + NEGRO + '"/>' +
    "</g>"),

  prohibido_estacionar: envolver(
    '<circle cx="50" cy="50" r="44" fill="' + AZUL + '" stroke="' + ROJO + '" stroke-width="9"/>' +
    '<line x1="22" y1="78" x2="78" y2="22" stroke="' + ROJO + '" stroke-width="9"/>'),

  prohibido_parar: envolver(
    '<circle cx="50" cy="50" r="44" fill="' + AZUL + '" stroke="' + ROJO + '" stroke-width="9"/>' +
    '<line x1="22" y1="78" x2="78" y2="22" stroke="' + ROJO + '" stroke-width="8"/>' +
    '<line x1="22" y1="22" x2="78" y2="78" stroke="' + ROJO + '" stroke-width="8"/>'),

  fin_prohibiciones: envolver(
    '<circle cx="50" cy="50" r="44" fill="#fff" stroke="#9aa3af" stroke-width="5"/>' +
    '<line x1="26" y1="76" x2="74" y2="24" stroke="' + NEGRO + '" stroke-width="5"/>' +
    '<line x1="33" y1="79" x2="81" y2="27" stroke="' + NEGRO + '" stroke-width="5"/>'),

  // ---------- ПРЕДПИСАНИЯ ----------
  sentido_obligatorio: envolver(
    circuloAzul +
    '<path d="M50 78 V24 M50 24 L34 42 M50 24 L66 42" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),

  giro_obligatorio: envolver(
    circuloAzul +
    '<path d="M36 76 V52 Q36 36 54 36 H70" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' +
    '<polygon points="66,22 86,36 66,50" fill="#fff"/>'),

  via_ciclistas: envolver(circuloAzul + bicicleta(50, 50, 1.5, "#fff")),

  // ---------- ПРИОРИТЕТ ----------
  calzada_prioridad: envolver(
    '<polygon points="50,5 95,50 50,95 5,50" fill="' + AMARILLO + '" stroke="#fff" stroke-width="7"/>'),

  fin_prioridad: envolver(
    '<polygon points="50,5 95,50 50,95 5,50" fill="' + AMARILLO + '" stroke="#fff" stroke-width="7"/>' +
    '<line x1="22" y1="78" x2="78" y2="22" stroke="' + NEGRO + '" stroke-width="6"/>'),

  // ---------- ПРЕДУПРЕЖДЕНИЯ ----------
  otros_peligros: envolver(
    trianguloPeligro +
    '<text x="50" y="78" text-anchor="middle" font-size="46" font-weight="bold" fill="' + NEGRO + '" font-family="Arial, sans-serif">!</text>'),

  curva_derecha: envolver(
    trianguloPeligro +
    '<path d="M42 78 Q42 56 58 48 Q68 43 62 32" stroke="' + NEGRO + '" stroke-width="7" fill="none" stroke-linecap="round"/>' +
    '<polygon points="55,34 72,26 68,44" fill="' + NEGRO + '"/>'),

  estrechamiento: envolver(
    trianguloPeligro +
    '<path d="M30 80 L38 46 M70 80 L62 46" stroke="' + NEGRO + '" stroke-width="7" stroke-linecap="round"/>'),

  baden: envolver(
    trianguloPeligro +
    '<path d="M26 74 Q50 40 74 74" stroke="' + NEGRO + '" stroke-width="7" fill="none" stroke-linecap="round"/>'),

  semaforo: envolver(
    trianguloPeligro +
    '<rect x="41" y="30" width="18" height="46" rx="4" fill="' + NEGRO + '"/>' +
    '<circle cx="50" cy="40" r="5" fill="#ef4444"/><circle cx="50" cy="53" r="5" fill="' + AMARILLO + '"/>' +
    '<circle cx="50" cy="66" r="5" fill="#22c55e"/>'),

  peatones_peligro: envolver(trianguloPeligro + peaton(50, 62, 1.25)),

  ciclistas_peligro: envolver(trianguloPeligro + bicicleta(50, 62, 1.15)),

  paso_a_nivel: envolver(
    '<line x1="12" y1="12" x2="88" y2="88" stroke="' + ROJO + '" stroke-width="12" stroke-linecap="round"/>' +
    '<line x1="88" y1="12" x2="12" y2="88" stroke="' + ROJO + '" stroke-width="12" stroke-linecap="round"/>' +
    '<line x1="20" y1="20" x2="80" y2="80" stroke="#fff" stroke-width="4" stroke-linecap="round"/>' +
    '<line x1="80" y1="20" x2="20" y2="80" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'),

  // ---------- УКАЗАНИЯ ----------
  estacionamiento: envolver(
    cuadradoAzul +
    '<text x="50" y="72" text-anchor="middle" font-size="60" font-weight="bold" fill="#fff" font-family="Arial, sans-serif">P</text>'),

  paso_peatones: envolver(
    cuadradoAzul +
    '<g fill="#fff"><rect x="22" y="72" width="8" height="14"/><rect x="34" y="72" width="8" height="14"/>' +
    '<rect x="46" y="72" width="8" height="14"/><rect x="58" y="72" width="8" height="14"/>' +
    '<rect x="70" y="72" width="8" height="14"/></g>' +
    peaton(50, 46, 1.3, "#fff")),
};

if (typeof module !== "undefined") module.exports = SENALES;
