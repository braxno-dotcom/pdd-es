# -*- coding: utf-8 -*-
"""Собирает страницы теста из одного шаблона.

Почему генератором, а не руками: у французского сайта банк вопросов вшит в каждую
из семи страниц (по 136 КБ на файл), и правка правила означает семь правок. Тут
банк один — `preguntas.js`, а страницы тонкие. Меняешь шаблон — пересобираешь всё:

    python generar.py
"""
import io

PLANTILLA = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<meta name="keywords" content="{claves}">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descripcion}">
<meta name="theme-color" content="#0f172a">
<link rel="canonical" href="https://braxno-dotcom.github.io/pdd-es/{archivo}">
<link rel="manifest" href="manifest.json">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%230f172a' stroke='%231a56db' stroke-width='4'/><text x='50' y='40' text-anchor='middle' font-size='20' font-weight='bold' fill='%2360a5fa'>DGT</text><text x='50' y='62' text-anchor='middle' font-size='13' fill='white'>España</text><text x='50' y='80' text-anchor='middle' font-size='13' fill='%23f87171'>RU</text></svg>">
<link rel="stylesheet" href="estilo.css">
</head>
<body>

<header>
  <div class="caja">
    <a class="inicio" href="index.html">← все темы</a>
    <h1>{h1}</h1>
    <p>{subtitulo}</p>
  </div>
</header>

<main>
  <div class="tarjeta">
    <div class="marcador"><span id="contador"></span><span id="puntos"></span></div>
    <div class="barra"><div id="barra"></div></div>
    <div id="zona"></div>
  </div>

  <div class="tarjeta">
    <h2>{titulo_texto}</h2>
    {texto}
  </div>

  <div class="lucia">
    <h2>Спросить голосом</h2>
    <p>Люси разберёт испанскую формулировку по словам и объяснит правило по-русски.</p>
    <a class="boton lucia" href="https://repetiteur.onrender.com/?c=es-pdd">Открыть Люси</a>
  </div>
</main>

<footer>
  <a href="index.html">ПДД Испании на русском</a> · тренажёр теории DGT<br>
  Официальный источник: <a href="https://www.dgt.es" rel="nofollow">dgt.es</a>
</footer>

<script>window.MODO = {modo};</script>
<script src="preguntas.js"></script>
<script src="motor.js"></script>
</body>
</html>
"""

PAGINAS = [
    dict(
        archivo="test.html",
        modo='{tema: null, examen: true}',
        titulo="Тест ПДД Испании — экзамен DGT на русском, 30 вопросов",
        h1="Экзамен DGT: 30 вопросов",
        subtitulo="Больше трёх ошибок — незачёт, как на настоящем экзамене",
        descripcion="Бесплатный тест ПДД Испании на русском: 30 вопросов вперемешку, максимум 3 ошибки — как на теоретическом экзамене DGT. Вопрос по-испански и перевод рядом.",
        claves="тест ПДД Испании, экзамен DGT на русском, тест DGT, теория на права Испания, examen teórico DGT ruso",
        titulo_texto="Как считают на экзамене",
        texto="""<p>Теоретический экзамен DGT — тридцать вопросов, и больше трёх ошибок означает
    незачёт. Здесь тот же счёт: как только четвёртая ошибка — тест закрывается и показывает разбор.</p>
    <p>Вопросы даются по-испански, как в зале, с переводом под ними. Варианты ответа каждый раз
    перемешиваются, чтобы не запоминалось место, а запоминалось правило.</p>
    <p class="nota-pie">Сдал теорию — на практику есть два года.</p>""",
    ),
    dict(
        archivo="velocidad.html",
        modo='{tema: "velocidad", examen: false}',
        titulo="Скорость в Испании — лимиты, тест на русском | ПДД Испании",
        h1="Скорость",
        subtitulo="Лимиты в городе, на трассе и в жилых зонах",
        descripcion="Ограничения скорости в Испании на русском: 120 на автомагистрали, 90 на обычной дороге, 30 и 50 в городе, 20 на единой платформе. Тест с переводом.",
        claves="скорость в Испании, лимит скорости Испания, 30 км/ч Испания, velocidad España, ПДД Испании скорость",
        titulo_texto="Коротко о лимитах",
        texto="""<ul>
      <li><b>120</b> км/ч — автомагистраль (<span lang="es">autopista, autovía</span>).</li>
      <li><b>90</b> км/ч — обычная загородная дорога.</li>
      <li><b>50</b> км/ч — город, если полос в одну сторону две и больше.</li>
      <li><b>30</b> км/ч — город, одна полоса в каждую сторону. Это главная перемена
          последних лет: с мая 2021 года большинство городских улиц именно тридцатые.</li>
      <li><b>20</b> км/ч — улицы, где тротуар и проезжая часть на одном уровне.</li>
    </ul>
    <p class="nota-pie">Дождь в Испании лимит автоматически не снижает — в отличие от Франции.
    Но обязанность вести машину по условиям остаётся.</p>""",
    ),
    dict(
        archivo="senales.html",
        modo='{tema: "senales", examen: false}',
        titulo="Дорожные знаки Испании на русском — формы, цвета, тест",
        h1="Знаки и разметка",
        subtitulo="По форме и цвету знак читается раньше, чем по картинке",
        descripcion="Дорожные знаки Испании на русском: треугольник — опасность, круг с красной каймой — запрет, синий круг — предписание. Разметка и светофоры. Тест с переводом.",
        claves="дорожные знаки Испании, señales de tráfico España, знаки Испании на русском, разметка Испания",
        titulo_texto="Как читать знак за секунду",
        texto="""<ul>
      <li><b>Треугольник с красной каймой</b> — предупреждение об опасности.</li>
      <li><b>Круг с красной каймой</b> — запрет или ограничение.</li>
      <li><b>Синий круг</b> — предписание: так делать обязательно.</li>
      <li><b>Синий квадрат</b> — указание и информация.</li>
      <li><b>Жёлтый фон</b> — временные знаки на ремонте: они главнее постоянных.</li>
    </ul>
    <p class="nota-pie">Если указания спорят между собой, главнее всех регулировщик,
    затем знаки, затем разметка.</p>""",
    ),
    dict(
        archivo="prioridad.html",
        modo='{tema: "prioridad", examen: false}',
        titulo="Приоритет и перекрёстки в Испании — тест на русском",
        h1="Приоритет",
        subtitulo="Круговые, перекрёстки, пешеходы, выезды",
        descripcion="Правила приоритета в Испании на русском: круговое движение, помеха справа, пешеходные переходы, выезд с парковки, полоса разгона. Тест с переводом.",
        claves="приоритет Испания, круговое движение Испания, glorieta prioridad, ПДД Испании перекрёсток",
        titulo_texto="Что чаще всего спрашивают",
        texto="""<ul>
      <li><b>Круговое:</b> приоритет у тех, кто уже едет внутри.</li>
      <li><b>Перекрёсток без знаков:</b> помеха справа.</li>
      <li><b>Выезд с парковки или частной территории:</b> уступаешь всем.</li>
      <li><b>Полоса разгона:</b> уступаешь тем, кто уже на магистрали.</li>
      <li><b>Разворот:</b> уступаешь всем, откуда бы они ни ехали.</li>
    </ul>""",
    ),
    dict(
        archivo="alcohol.html",
        modo='{tema: "alcohol", examen: false}',
        titulo="Алкоголь за рулём в Испании — нормы 0,25 и 0,15, тест на русском",
        h1="Алкоголь и лекарства",
        subtitulo="Нормы, проверки, что считается преступлением",
        descripcion="Нормы алкоголя за рулём в Испании: 0,25 мг/л в выдыхаемом воздухе и 0,5 г/л в крови, для новичков 0,15 и 0,3. Наркотики — нулевая терпимость. Тест на русском.",
        claves="алкоголь за рулём Испания, норма алкоголя Испания, tasa de alcohol España, 0,25 mg/l",
        titulo_texto="Цифры, которые надо знать наизусть",
        texto="""<ul>
      <li><b>0,25 мг/л</b> в выдыхаемом воздухе и <b>0,5 г/л</b> в крови — общая норма.</li>
      <li><b>0,15 мг/л</b> и <b>0,3 г/л</b> — новички и профессиональные водители.</li>
      <li><b>Наркотики</b> — нулевая терпимость, сам факт наличия в организме.</li>
      <li><b>Отказ от проверки</b> — уголовное дело, а не штраф.</li>
    </ul>
    <p class="nota-pie">Кофе и холодный душ ничего не убирают: алкоголь выводит только время.</p>""",
    ),
    dict(
        archivo="multas.html",
        modo='{tema: "multas", examen: false}',
        titulo="Штрафы и баллы в Испании — тест на русском, система puntos",
        h1="Штрафы и баллы",
        subtitulo="12 баллов, 8 у новичка, и за что их снимают",
        descripcion="Система баллов в Испании на русском: 12 баллов у обычного водителя, 8 у новичка, 15 после трёх лет без нарушений. Телефон в руке — минус 6. Скидка 50 % при оплате в 20 дней.",
        claves="штрафы Испания, баллы permiso por puntos, multas España, скидка 50% штраф Испания",
        titulo_texto="Система баллов коротко",
        texto="""<ul>
      <li><b>12 баллов</b> у обычного водителя, <b>8</b> у начинающего.</li>
      <li><b>15</b> — потолок после трёх лет без потерь.</li>
      <li><b>−6</b> за телефон в руке, <b>−4</b> за ремень и за красный свет.</li>
      <li><b>Скидка 50 %</b>, если заплатить в течение двадцати дней.</li>
      <li><b>Баллы кончились</b> — права теряют силу, возвращают их курсами.</li>
    </ul>""",
    ),
    dict(
        archivo="seguridad.html",
        modo='{tema: "seguridad", examen: false}',
        titulo="Безопасность и техника в Испании — V-16, ремни, дети, ITV",
        h1="Безопасность и машина",
        subtitulo="Маячок V-16, ремни, дети, шины, техосмотр",
        descripcion="Безопасность за рулём в Испании на русском: маячок V-16 вместо треугольников с 1 января 2026, детские кресла до 135 см, ITV каждые два года, протектор 1,6 мм.",
        claves="V-16 Испания, baliza V16, детское кресло Испания, ITV Испания, безопасность ПДД Испании",
        titulo_texto="Что изменилось в 2026 году",
        texto="""<p><b>Треугольники больше не работают.</b> С 1 января 2026 года при поломке или
    аварии машину обозначают светящимся маячком <b>V-16</b> с подключением: его ставят на крышу,
    не выходя на проезжую часть, и он сам сообщает о месте в систему DGT.</p>
    <ul>
      <li><b>Жилет</b> надевают до того, как выйти из машины на дорогу.</li>
      <li><b>Дети ниже 135 см</b> — только сзади и в удерживающем устройстве.</li>
      <li><b>ITV</b> для легковой машины 4-10 лет — раз в два года.</li>
      <li><b>Протектор</b> — не меньше 1,6 мм.</li>
    </ul>""",
    ),
    dict(
        archivo="documentos.html",
        modo='{tema: "documentos", examen: false}',
        titulo="Права в Испании — документы, экзамен, обмен прав (canje)",
        h1="Документы и экзамен",
        subtitulo="Категории, сроки, обмен иностранных прав",
        descripcion="Права в Испании на русском: экзамен DGT из 30 вопросов, категория B с 18 лет, продление раз в 10 лет, обмен иностранных прав только со странами, имеющими соглашение.",
        claves="права в Испании, обмен прав Испания, canje permiso conducir, DGT экзамен, документы на машину Испания",
        titulo_texto="Про обмен прав — без слухов",
        texto="""<p>Обменять иностранные права на испанские (<span lang="es">canje</span>) можно
    <b>только если у Испании есть соглашение с твоей страной</b>. Список стран-участниц —
    на <a href="https://www.dgt.es" rel="nofollow">dgt.es</a>, и это единственное место, где его
    стоит смотреть: в чатах список устаревает и обрастает домыслами.</p>
    <p>Само дело ведёт <span lang="es">Jefatura Provincial de Tráfico</span> твоей провинции —
    туда же вопросы про язык экзамена и про запись <span lang="es">«por libre»</span>, без автошколы.
    Ответ зависит от провинции.</p>
    <p class="nota-pie">Документы на машину: <span lang="es">permiso de circulación</span>,
    <span lang="es">ficha técnica</span> и страховка.</p>""",
    ),
]


def main():
    for p in PAGINAS:
        html = PLANTILLA.format(**p)
        io.open(p["archivo"], "w", encoding="utf-8").write(html)
        print("собрано:", p["archivo"])

    # Карта сайта — чтобы поисковик увидел все темы, а не одну главную.
    hoy = "2026-09-16"
    urls = ["index.html"] + [p["archivo"] for p in PAGINAS]
    mapa = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        loc = "https://braxno-dotcom.github.io/pdd-es/" + ("" if u == "index.html" else u)
        prioridad = "1.0" if u == "index.html" else "0.8"
        mapa.append("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
                    % (loc, hoy, prioridad))
    mapa.append("</urlset>")
    io.open("sitemap.xml", "w", encoding="utf-8").write("\n".join(mapa) + "\n")
    print("собрано: sitemap.xml")


if __name__ == "__main__":
    main()
