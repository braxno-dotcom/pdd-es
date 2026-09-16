/* Дорожная разметка и сигналы светофора — нарисованы, и по-другому нельзя.

   ⚠️ Это НЕ знаки. В официальном каталоге знаков их нет: разметка живёт на асфальте,
   а не на столбе, и «скачать картинку сплошной линии» неоткуда — её рисуют куском
   дороги. То же со светофором: в каталоге есть треугольник-предупреждение о нём
   (P-3, он скачан), а сам горящий сигнал надо показать самому.

   Всё остальное — знаки — берётся из официального каталога, см. senales.js. */

const MARCAS = {
  // Полоса асфальта сверху вниз, как её видит водитель.
  marca_continua:
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
    '<rect width="100" height="100" fill="#4b5563"/>' +
    '<rect x="8" y="0" width="4" height="100" fill="#fff"/>' +
    '<rect x="88" y="0" width="4" height="100" fill="#fff"/>' +
    '<rect x="48" y="0" width="5" height="100" fill="#fff"/></svg>',

  marca_doble:
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
    '<rect width="100" height="100" fill="#4b5563"/>' +
    '<rect x="8" y="0" width="4" height="100" fill="#fff"/>' +
    '<rect x="88" y="0" width="4" height="100" fill="#fff"/>' +
    '<rect x="43" y="0" width="5" height="100" fill="#fff"/>' +
    '<rect x="53" y="0" width="5" height="100" fill="#fff"/></svg>',

  marca_discontinua:
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
    '<rect width="100" height="100" fill="#4b5563"/>' +
    '<rect x="8" y="0" width="4" height="100" fill="#fff"/>' +
    '<rect x="88" y="0" width="4" height="100" fill="#fff"/>' +
    '<g fill="#fff"><rect x="48" y="2" width="5" height="16"/><rect x="48" y="26" width="5" height="16"/>' +
    '<rect x="48" y="50" width="5" height="16"/><rect x="48" y="74" width="5" height="16"/></g></svg>',

  // Жёлтый зигзаг вдоль бордюра: стоянка запрещена.
  marca_zigzag:
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
    '<rect width="100" height="100" fill="#4b5563"/>' +
    '<rect x="0" y="0" width="22" height="100" fill="#9ca3af"/>' +
    '<path d="M30 4 L46 16 L30 28 L46 40 L30 52 L46 64 L30 76 L46 88 L30 96" ' +
    'stroke="#f1bf00" stroke-width="7" fill="none" stroke-linejoin="round"/></svg>',

  // Светофор: постоянный жёлтый и мигающий жёлтый — разные вещи, и спрашивают обе.
  semaforo_ambar:
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
    '<rect x="30" y="6" width="40" height="88" rx="8" fill="#1f2937"/>' +
    '<circle cx="50" cy="26" r="11" fill="#4b5563"/>' +
    '<circle cx="50" cy="50" r="11" fill="#f1bf00"/>' +
    '<circle cx="50" cy="74" r="11" fill="#4b5563"/></svg>',

  semaforo_ambar_intermitente:
    '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">' +
    '<rect x="34" y="24" width="32" height="52" rx="7" fill="#1f2937"/>' +
    '<circle cx="50" cy="50" r="13" fill="#f1bf00"/>' +
    '<g stroke="#f1bf00" stroke-width="4" stroke-linecap="round">' +
    '<path d="M50 20 V10 M50 80 V90 M20 50 H10 M80 50 H90"/>' +
    '<path d="M28 28 L21 21 M72 28 L79 21 M28 72 L21 79 M72 72 L79 79"/></g></svg>',
};

if (typeof module !== "undefined") module.exports = MARCAS;
