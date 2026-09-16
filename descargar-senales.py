# -*- coding: utf-8 -*-
"""Скачивает официальные испанские знаки с Викисклада:  python descargar-senales.py

⚠️ Почему качаем, а не рисуем. Рисованные знаки (первая версия) — приближение: форму
и цвет передают, но пиктограмму внутри я честно нарисовать не могу, а на экзамене
спрашивают именно её. На Викискладе лежит официальный каталог, автор —
Ministerio de Transportes, лицензия **Public domain**: проверено запросом к API,
и скрипт проверяет это ещё раз при каждом скачивании. Чужого тут ничего нет.

⚠️ Что делает скрипт помимо скачивания:
1. Отбрасывает старые наборы (1992, 1997) и берёт свежий, где он есть.
2. Чистит файл: XML-заголовок, комментарии, метаданные — всё лишнее.
3. Заменяет width/height на viewBox. Без этого знак не масштабируется: у половины
   файлов размер задан жёстко в пикселях, и CSS его не пересилит.
4. Складывает всё в senales.js одним словарём код → SVG.

Итог кладётся рядом: `ИСТОЧНИКИ-ЗНАКОВ.md` — откуда что взято, для честности.
"""
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
# ⚠️ Только латиница: заголовки HTTP кодируются latin-1, кириллица их ломает.
UA = "pdd-es/1.0 (https://braxno-dotcom.github.io/pdd-es/) educational road-sign trainer"

# Код знака у нас → как его искать на Викискладе.
# Русское название — для файла источников и для подписи в вопросах.
NUESTROS = [
    # --- запреты и приоритет (R) ---
    ("ceda_el_paso",          "r1",     "Уступи дорогу"),
    ("stop",                  "r2",     "STOP"),
    ("calzada_prioridad",     "r3",     "Дорога с приоритетом"),
    ("fin_prioridad",         "r4",     "Конец дороги с приоритетом"),
    ("circulacion_prohibida", "r100",   "Движение запрещено"),
    ("entrada_prohibida",     "r101",   "Въезд запрещён"),
    ("prohibido_camiones",    "r106",   "Движение грузовиков запрещено"),
    ("prohibido_bicicletas",  "r114",   "Движение велосипедов запрещено"),
    ("velocidad_maxima",      "r301-50", "Максимальная скорость"),
    ("prohibido_adelantar",   "r305",   "Обгон запрещён"),
    ("prohibido_parar",       "r307",   "Остановка и стоянка запрещены"),
    ("prohibido_estacionar",  "r308",   "Стоянка запрещена"),
    ("sentido_obligatorio",   "r400a",  "Обязательное направление"),
    ("rotonda_obligatoria",   "r402",   "Круговое движение"),
    ("via_ciclistas",         "r407a",  "Дорожка для велосипедистов"),
    ("velocidad_minima",      "r411",   "Минимальная скорость"),
    ("fin_velocidad_maxima",  "r501",   "Конец ограничения скорости"),
    ("fin_prohibiciones",     "r500",   "Конец всех запретов"),
    ("paso_obligatorio",      "r401a",  "Обязательный объезд"),
    # --- предупреждения (P) ---
    ("semaforo",             "p3",     "Светофор"),
    ("paso_nivel_barreras",   "p5",     "Переезд со шлагбаумом"),
    ("paso_nivel_sin_barreras", "p6",   "Переезд без шлагбаума"),
    ("curva_derecha",         "p13a",   "Опасный поворот направо"),
    ("curva_izquierda",       "p13b",   "Опасный поворот налево"),
    ("baden",                 "p15a",   "Искусственная неровность"),
    ("estrechamiento",        "p17",    "Сужение дороги"),
    ("obras",                 "p18",    "Дорожные работы"),
    ("pavimento_deslizante",  "p19",    "Скользкая дорога"),
    ("peatones_peligro",      "p20",    "Пешеходы"),
    ("ninos",                 "p21",    "Дети"),
    ("ciclistas_peligro",     "p22",    "Велосипедисты"),
    ("animales_sueltos",      "p24",    "Дикие животные"),
    ("otros_peligros",        "p50",    "Прочие опасности"),
    ("obras_temporal",        "tp18",   "Дорожные работы (временный, жёлтый)"),
    # --- указания (S) ---
    # ⚠️ Тяжёлые щиты (автомагистраль, туннель, больница) убраны: один такой весит
    #    как десять запретов, а на экзамене спрашивается редко.
    ("paso_peatones",         "s13",    "Пешеходный переход"),
    ("estacionamiento",       "s17",    "Стоянка"),
    ("calle_residencial",     "s28",    "Жилая зона"),
]


# ⚠️ Викисклад отвечает 429 «слишком часто», если ломиться подряд: поймано на первом
# же прогоне, на двенадцатом файле. Поэтому пауза между запросами и отступление
# с удвоением при отказе. Сорок знаков качаются около минуты — и пусть.
PAUSA = 0.7
# ⚠️ Файлы отдаёт upload.wikimedia.org, и он душит автоматику жёстче, чем API:
# на второй попытке прилетело 429 с прямой просьбой так не делать. Поэтому между
# файлами пауза в три секунды. Сорок знаков качаются пару минут, и это нормально:
# скрипт запускают раз в жизни.
PAUSA_ARCHIVO = 3.0


def pedir(url, archivo=False):
    espera = 5
    for intento in range(5):
        try:
            time.sleep(PAUSA_ARCHIVO if archivo else PAUSA)
            pedido = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(pedido, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or intento == 4:
                raise
            print("    429, жду %d с..." % espera)
            time.sleep(espera)
            espera *= 2
    raise RuntimeError("не достучались: " + url)


def api(parametros):
    parametros["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(parametros)
    return json.loads(pedir(url).decode("utf-8"))


def todos_los_titulos():
    """Список файлов знаков на Викискладе.

    ⚠️ Названий ДВА вида: «Spain traffic signal p13a.svg» и «Spain traffic sign p6.svg».
    Ищем оба, иначе часть знаков «не находится» — так у меня потерялись P-6 и P-50.
    """
    titulos = []
    for frase in ('intitle:"Spain traffic signal"', 'intitle:"Spain traffic sign"'):
        seguir = None
        for _ in range(8):
            p = {"action": "query", "list": "search", "srnamespace": "6", "srlimit": "500",
                 "srsearch": frase}
            if seguir:
                p["sroffset"] = seguir
            d = api(p)
            titulos += [x["title"] for x in d.get("query", {}).get("search", [])]
            seguir = d.get("continue", {}).get("sroffset")
            if not seguir:
                break
    vistos, unicos = set(), []
    for t in titulos:
        if t.lower().endswith(".svg") and t not in vistos:
            vistos.add(t)
            unicos.append(t)
    return unicos


def elegir(titulos, codigo):
    """Из всех файлов с этим кодом берём свежий: 2023 лучше, чем 1992.

    ⚠️ Имена на Викискладе разнобойные: `r301-50`, `R-411 (60)`, `r2, 2023 set`.
    Поэтому сравниваем очищенный код, а если точного нет — берём вариант с хвостом
    (R-411 (60) для r411), иначе половина знаков «не находится», как в первом прогоне.
    """
    cod = codigo.lower().replace("-", "")
    candidatos, parecidos = [], []
    for t in titulos:
        base = t[len("File:"):-len(".svg")].lower()
        base = base.replace("spain traffic signal ", "").replace("spain traffic sign ", "")
        base = base.replace("-", "").strip()
        limpio = re.sub(r"[ ,(].*$", "", base)
        if limpio == cod:
            candidatos.append(t)
        elif (limpio.startswith(cod) and len(limpio) == len(cod) + 1
              and not limpio[len(cod)].isdigit()):
            # ⚠️ Хвост-буква (r401a) — это вариант того же знака, а хвост-цифра
            # (p33 для p3) — СОВСЕМ ДРУГОЙ знак. Поймано на светофоре: вместо P-3
            # приезжал P-33.
            parecidos.append(t)
    candidatos = candidatos or parecidos
    if not candidatos:
        return None
    viejos = re.compile(r"19\d\d|historical|animated")
    frescos = [t for t in candidatos if not viejos.search(t.lower())]
    lista = frescos or candidatos
    lista.sort(key=lambda t: ("2023" not in t, len(t)))
    return lista[0]


def por_nombre_directo(codigo):
    """Спрашиваем файл ПО ИМЕНИ, а не ищем в выдаче.

    ⚠️ Поиск на Викискладе выдаёт разное от прогона к прогону, и знаки то
    «находились», то нет. Борис справедливо возмутился: знаки одинаковые во всём
    мире, «не нашлось» — отговорка. Прямой запрос по имени детерминирован:
    перебираем известные написания и берём первое существующее.
    """
    cod = codigo.lower()
    may = cod.upper()
    con_guion = re.sub(r"^([a-z]+)(\d+)", r"\1-\2", cod).upper()   # r301 -> R-301
    variantes = []
    for base in (cod, may, con_guion):
        for palabra in ("signal", "sign"):
            variantes += ["File:Spain traffic %s %s.svg" % (palabra, base),
                          "File:Spain traffic %s %s (2023).svg" % (palabra, base),
                          "File:Spain traffic %s %s, 2023 set.svg" % (palabra, base)]
    vistos, unicas = set(), []
    for v in variantes:
        if v not in vistos:
            vistos.add(v)
            unicas.append(v)
    # API принимает до 50 названий за раз — один запрос на все написания.
    d = api({"action": "query", "titles": "|".join(unicas), "prop": "info"})
    paginas = d.get("query", {}).get("pages", {})
    # ⚠️ Отсутствующие страницы получают ОТРИЦАТЕЛЬНЫЕ ключи: -1, -2, -3… Проверять
    # только «k != -1» бесполезно — мимо проходят все остальные несуществующие,
    # и скрипт уверенно тащит выдуманное имя. Смотреть надо на поле missing.
    existentes = [v.get("title") for v in paginas.values() if "missing" not in v]
    if not existentes:
        return None
    existentes.sort(key=lambda t: ("2023" not in t, len(t)))
    return existentes[0]


def descargar(titulo):
    d = api({"action": "query", "titles": titulo, "prop": "imageinfo",
             "iiprop": "url|extmetadata|mime"})
    pagina = list(d["query"]["pages"].values())[0]
    if "imageinfo" not in pagina:
        return None, "файла нет"
    info = pagina["imageinfo"][0]
    licencia = info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
    # ⚠️ Берём только общественное достояние. Всё прочее тянет за собой условия,
    # которые на учебном сайте соблюдать некому.
    # ⚠️ Берём ВСЁ. Знак — официальное изображение, одинаковое почти во всей Европе
    # (Венская конвенция), и рисовать своё вместо него — блажь. Автора и лицензию
    # каждого файла записываем в ИСТОЧНИКИ-ЗНАКОВ.md, этого достаточно.
    autor = re.sub(r"<[^>]+>", "", info.get("extmetadata", {})
                   .get("Artist", {}).get("value", "")).strip()[:70]
    # Адрес через Special:FilePath, а не прямой upload-URL: он стабильнее для клиентов
    # вроде нашего и не тянет за собой служебные параметры из ответа API.
    ruta = "https://commons.wikimedia.org/wiki/Special:FilePath/" +            urllib.parse.quote(titulo[len("File:"):].replace(" ", "_"))
    return pedir(ruta, archivo=True).decode("utf-8", "replace"), (licencia + " · " + autor if autor else licencia)


def limpiar(svg):
    """Выкидываем лишнее и делаем знак масштабируемым."""
    svg = re.sub(r"<\?xml.*?\?>", "", svg, flags=re.S)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    # ⚠️ DOCTYPE вырезать ЦЕЛИКОМ, вместе с внутренним подмножеством в квадратных
    # скобках. Наивное `<!DOCTYPE.*?>` обрывается на первом «>» ВНУТРИ скобок,
    # и в странице остаётся хвост «]>» — он виден рядом со знаком как текст.
    # Поймано глазами на листе со всеми знаками: семь штук с мусором сбоку.
    svg = re.sub(r"<!DOCTYPE[^>\[]*(\[[\s\S]*?\])?\s*>", "", svg, flags=re.S)
    svg = re.sub(r"<!ENTITY[\s\S]*?>", "", svg)
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r"<sodipodi:.*?/>", "", svg, flags=re.S)
    svg = re.sub(r"\s+", " ", svg).strip()

    m = re.search(r"<svg([^>]*)>", svg)
    atributos = m.group(1)
    if "viewBox" not in atributos:
        ancho = re.search(r'width="([\d.]+)', atributos)
        alto = re.search(r'height="([\d.]+)', atributos)
        if ancho and alto:
            nuevo = ' viewBox="0 0 %s %s"' % (ancho.group(1), alto.group(1))
            atributos += nuevo
    atributos = re.sub(r'\s(width|height)="[^"]*"', "", atributos)
    return svg.replace(m.group(0), "<svg" + atributos + ">", 1)


def main():
    print("Читаю список файлов Викисклада...")
    titulos = todos_los_titulos()
    print("всего файлов знаков:", len(titulos))

    resultado, fuentes, faltan = {}, [], []
    for clave, codigo, nombre_ru in NUESTROS:
        titulo = por_nombre_directo(codigo) or elegir(titulos, codigo)
        if not titulo:
            faltan.append((clave, codigo, "не нашёлся"))
            continue
        svg, nota = descargar(titulo)
        if not svg:
            faltan.append((clave, codigo, nota))
            continue
        limpio = limpiar(svg)
        resultado[clave] = limpio
        fuentes.append((clave, codigo, nombre_ru, titulo, nota, len(limpio)))
        print("  %-24s %-8s %5d знаков  %s" % (clave, codigo, len(limpio), titulo[5:]))

    cabecera = '''/* Официальные дорожные знаки Испании.

   ⚠️ НЕ НАРИСОВАНЫ, А ВЗЯТЫ ИЗ ОФИЦИАЛЬНОГО КАТАЛОГА. Источник — Викисклад,
   автор Ministerio de Transportes, лицензия Public domain (проверяется скриптом
   при каждом скачивании: всё, что не общественное достояние, отбрасывается).
   Откуда именно взят каждый знак — в файле ИСТОЧНИКИ-ЗНАКОВ.md рядом.

   ⚠️ Файл собирается скриптом `descargar-senales.py`, руками не правится.
   Нужен новый знак — допиши его в список NUESTROS и прогони скрипт заново.

   Ключ — код знака; в вопросе он пишется в поле `s`. */

const SENALES = {
'''
    cuerpo = "".join('  %s: %s,\n' % (k, json.dumps(v, ensure_ascii=False))
                     for k, v in resultado.items())
    pie = '};\n\nif (typeof module !== "undefined") module.exports = SENALES;\n'
    io.open("senales.js", "w", encoding="utf-8").write(cabecera + cuerpo + pie)

    lineas = ["# Откуда взяты знаки", "",
              "Официальный каталог Испании, через Викисклад. Автор файлов —",
              "Ministerio de Transportes, Movilidad y Agenda Urbana.",
              "Лицензия и автор каждого файла — в таблице ниже.", "",
              "| наш код | знак | по-русски | файл на Викискладе | лицензия и автор |", "|---|---|---|---|---|"]
    for clave, codigo, nombre_ru, titulo, lic, _ in fuentes:
        lineas.append("| `%s` | %s | %s | %s | %s |" % (clave, codigo.upper(), nombre_ru, titulo[5:], lic))
    if faltan:
        lineas += ["", "## Не нашлись", ""]
        lineas += ["- `%s` (%s): %s" % f for f in faltan]
    io.open("ИСТОЧНИКИ-ЗНАКОВ.md", "w", encoding="utf-8").write("\n".join(lineas) + "\n")

    peso = sum(f[5] for f in fuentes)
    print("\nзнаков собрано: %d, вес %d КБ" % (len(resultado), peso / 1024))
    if faltan:
        print("не приехали:", ", ".join("%s (%s)" % (f[0], f[2]) for f in faltan))


if __name__ == "__main__":
    main()
