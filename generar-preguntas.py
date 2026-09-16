# -*- coding: utf-8 -*-
"""Собирает вопросы из таблиц правил:  python generar-preguntas.py

⚠️ ЗАЧЕМ ГЕНЕРАТОР, А НЕ РУКИ. Банк нужен на тысячу вопросов, а рука выдыхается
к третьей сотне: формулировки мельчают, а факты начинают плыть — и это худшее,
что может случиться с тренажёром. Настоящие банки устроены так же: половина
вопросов — вариации одного правила («какая скорость у ГРУЗОВИКА на автомагистрали»,
«…у автобуса», «…с прицепом»), и составляются они по таблице, а не сочиняются.

Правило здесь записано ОДИН раз, в таблице. Ошибёшься в таблице — ошибка поедет
во все вопросы разом, зато и правится она в одном месте. Сочинённый руками вопрос
так не проверишь.

Что генератор НЕ делает: он не пишет вопросы «на понимание» — про приоритет
в конкретной ситуации, про поведение в тумане, про то, что делать при аварии.
Такие остаются рукописными, они лежат в preguntas.js и генератором не трогаются.

Результат кладётся в preguntas-auto.js отдельным файлом: рукописный банк
не перемешивается с машинным, и пересобрать машинный можно в любой момент.
"""
import io
import json
import random
import subprocess

random.seed(20260916)          # ⚠️ Фиксированное зерно: пересборка не должна
                               # тасовать банк и ломать историю правок.

# ============================ СКОРОСТЬ ============================
# Таблица испанских лимитов. Источник — Reglamento General de Circulación,
# сверено на сентябрь 2026. Меняется правило — меняется одна строка.
VIAS = {
    "autopista": ("autopista o autovía", "автомагистрали"),
    "convencional": ("carretera convencional", "обычной загородной дороге"),
    "urbana_2": ("vía urbana de dos carriles por sentido", "городской дороге с двумя полосами в одну сторону"),
    "urbana_1": ("vía urbana de un carril por sentido", "городской улице с одной полосой в каждую сторону"),
    "plataforma": ("calle de plataforma única", "улице с единым уровнем тротуара и проезжей части"),
    "residencial": ("zona residencial", "жилой зоне"),
}
VEHICULOS = {
    "turismo": ("un turismo", "легковому автомобилю"),
    "camion": ("un camión de más de 3.500 kg", "грузовику тяжелее 3500 кг"),
    "autobus": ("un autobús", "автобусу"),
    "remolque": ("un turismo con remolque ligero", "легковому с лёгким прицепом"),
    "motocicleta": ("una motocicleta", "мотоциклу"),
}
# Лимит в км/ч: (вид дороги, вид транспорта) → сколько.
LIMITES = {
    ("autopista", "turismo"): 120, ("autopista", "camion"): 90,
    ("autopista", "autobus"): 100, ("autopista", "remolque"): 90,
    ("autopista", "motocicleta"): 120,
    ("convencional", "turismo"): 90, ("convencional", "camion"): 80,
    ("convencional", "autobus"): 90, ("convencional", "remolque"): 70,
    ("convencional", "motocicleta"): 90,
    ("urbana_2", "turismo"): 50, ("urbana_2", "camion"): 50,
    ("urbana_2", "autobus"): 50, ("urbana_2", "motocicleta"): 50,
    ("urbana_1", "turismo"): 30, ("urbana_1", "camion"): 30,
    ("urbana_1", "autobus"): 30, ("urbana_1", "motocicleta"): 30,
    ("plataforma", "turismo"): 20, ("plataforma", "motocicleta"): 20,
    ("residencial", "turismo"): 20, ("residencial", "motocicleta"): 20,
}

PLANTILLAS_VELOCIDAD = [
    ("En {via}, {vehiculo} puede circular como máximo a:",
     "По {via_ru} {vehiculo_ru} разрешено максимум:"),
    ("¿Cuál es la velocidad máxima de {vehiculo} en {via}?",
     "Какова максимальная скорость {vehiculo_ru} по {via_ru}?"),
    ("El límite de velocidad de {vehiculo} en {via} es de:",
     "Ограничение скорости {vehiculo_ru} по {via_ru} составляет:"),
]


def distractores_velocidad(correcto):
    """Два неверных значения рядом с правильным — из той же сетки лимитов."""
    escala = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]
    cerca = [v for v in escala if v != correcto and abs(v - correcto) <= 40]
    random.shuffle(cerca)
    return cerca[:2]


def preguntas_velocidad():
    salida = []
    for (via, veh), limite in sorted(LIMITES.items()):
        for es, ru in PLANTILLAS_VELOCIDAD:
            via_es, via_ru = VIAS[via]
            veh_es, veh_ru = VEHICULOS[veh]
            malos = distractores_velocidad(limite)
            salida.append({
                "t": "velocidad",
                "q": es.format(via=via_es, vehiculo=veh_es),
                "q_ru": ru.format(via_ru=via_ru, vehiculo_ru=veh_ru),
                "o": ["%d km/h" % limite] + ["%d km/h" % m for m in malos],
                "o_ru": ["%d км/ч" % limite] + ["%d км/ч" % m for m in malos],
                "e": "По таблице лимитов: %s — %d км/ч." % (veh_ru.capitalize(), limite),
            })
    return salida


# ============================ БАЛЛЫ ============================
# Сколько баллов снимают. Правило записано один раз.
PUNTOS = [
    ("conducir sujetando el teléfono móvil con la mano", "держать телефон в руке за рулём", 6),
    ("conducir con una tasa de alcohol superior al doble de la permitida", "превысить норму алкоголя вдвое", 6),
    ("arrojar a la vía objetos que puedan provocar un incendio", "выбросить на дорогу то, что может вызвать пожар", 6),
    ("conducir con presencia de drogas en el organismo", "сесть за руль с наркотиками в организме", 6),
    ("no utilizar el cinturón de seguridad", "не пристегнуть ремень", 4),
    ("no respetar un semáforo en rojo", "проехать на красный", 4),
    ("no respetar la prioridad de paso", "не уступить дорогу, когда обязан", 4),
    ("adelantar poniendo en peligro a otros", "обогнать, создав опасность", 4),
    ("no utilizar el casco los motoristas", "мотоциклисту ехать без шлема", 4),
    ("circular marcha atrás en autopista", "ехать задним ходом по автомагистрали", 6),
    ("no mantener la distancia de seguridad", "не держать дистанцию", 4),
    ("conducir utilizando auriculares conectados al móvil", "ехать в наушниках, подключённых к телефону", 3),
]

PLANTILLAS_PUNTOS = [
    ("¿Cuántos puntos se pierden por {falta}?", "Сколько баллов снимают за то, что {falta_ru}?"),
    ("La sanción por {falta} supone la pérdida de:", "Наказание за то, что {falta_ru}, отнимает:"),
]


def preguntas_puntos():
    salida = []
    for falta_es, falta_ru, puntos in PUNTOS:
        otros = [p for p in (2, 3, 4, 6) if p != puntos]
        random.shuffle(otros)
        for es, ru in PLANTILLAS_PUNTOS:
            salida.append({
                "t": "multas",
                "q": es.format(falta=falta_es),
                "q_ru": ru.format(falta_ru=falta_ru),
                "o": ["%d puntos" % puntos] + ["%d puntos" % o for o in otros[:2]],
                "o_ru": ["%d балла" % puntos if puntos < 5 else "%d баллов" % puntos] +
                        ["%d балла" % o if o < 5 else "%d баллов" % o for o in otros[:2]],
                "e": "За это снимают %d." % puntos,
            })
    return salida


# ============================ ЗНАКИ ============================
# Каждому знаку — вопрос «что это значит» с разными формулировками.
# Значения берутся отсюда, а сами картинки лежат в senales.js по тем же ключам.
SIGNIFICADOS = [
    ("stop", "Detenerse por completo antes de la línea", "Полностью остановиться перед линией",
     ["Ceder el paso sin detenerse del todo", "Reducir la velocidad y continuar"],
     ["Уступить, не останавливаясь полностью", "Сбросить скорость и ехать дальше"]),
    ("ceda_el_paso", "Ceder el paso a quien circula por la otra vía", "Уступить дорогу тем, кто едет по другой дороге",
     ["Detenerse siempre del todo antes de la línea", "Tener prioridad sobre la otra vía"],
     ["Всегда остановиться перед линией", "Иметь приоритет над другой дорогой"]),
    ("calzada_prioridad", "Circular por una vía con prioridad", "Ехать по дороге с приоритетом",
     ["Ceder el paso en todos los cruces", "Entrar en una zona de prioridad peatonal"],
     ["Уступать на всех перекрёстках", "Въезжать в зону приоритета пешеходов"]),
    ("fin_prioridad", "Fin de la vía con prioridad", "Конец дороги с приоритетом",
     ["Comienzo de una vía con prioridad", "Prioridad sólo para vehículos pesados"],
     ["Начало дороги с приоритетом", "Приоритет только для грузовиков"]),
    ("circulacion_prohibida", "Circulación prohibida en ambos sentidos", "Движение запрещено в обе стороны",
     ["Fin de todas las prohibiciones", "Vía reservada a vehículos lentos"],
     ["Конец всех запретов", "Дорога только для тихоходных"]),
    ("entrada_prohibida", "Entrada prohibida: es sentido contrario", "Въезд запрещён: там встречное движение",
     ["Prohibido estacionar en todo ese lado", "Calle cortada por obras en curso"],
     ["Стоянка на той стороне запрещена", "Улица перекрыта из-за работ"]),
    ("prohibido_camiones", "Prohibido el paso a camiones de mercancías", "Проезд грузовиков запрещён",
     ["Prohibido el paso a autobuses de línea", "Prohibido el paso con remolque pesado"],
     ["Проезд автобусов запрещён", "Проезд с прицепом запрещён"]),
    ("prohibido_bicicletas", "Prohibido el paso a bicicletas", "Проезд велосипедов запрещён",
     ["Vía obligatoria para bicicletas", "Aparcamiento reservado a bicicletas"],
     ["Дорожка, обязательная для велосипедов", "Парковка для велосипедов"]),
    ("velocidad_maxima", "No superar la velocidad indicada", "Не превышать указанную скорость",
     ["Circular exactamente a esa velocidad", "Velocidad recomendada en el tramo"],
     ["Ехать ровно с этой скоростью", "Рекомендованная скорость на участке"]),
    ("velocidad_minima", "Velocidad mínima obligatoria", "Обязательная минимальная скорость",
     ["Velocidad máxima permitida", "Distancia mínima entre vehículos"],
     ["Максимально разрешённая скорость", "Минимальная дистанция между машинами"]),
    ("prohibido_adelantar", "Prohibido adelantar a otros vehículos", "Обгон других машин запрещён",
     ["Prohibido circular en paralelo", "Prohibido remolcar otro vehículo"],
     ["Запрещено ехать параллельно", "Запрещено буксировать другую машину"]),
    ("prohibido_parar", "Prohibido parar y estacionar", "Остановка и стоянка запрещены",
     ["Prohibido estacionar más de una hora", "Zona de carga y descarga"],
     ["Стоянка дольше часа запрещена", "Зона погрузки и разгрузки"]),
    ("prohibido_estacionar", "Prohibido estacionar en ese lado", "Стоянка на этой стороне запрещена",
     ["Prohibido parar ni un momento", "Aparcamiento de pago con ticket"],
     ["Нельзя даже остановиться", "Платная парковка по билету"]),
    ("sentido_obligatorio", "Sentido obligatorio en esa dirección", "Обязательное направление движения",
     ["Prohibido girar en esa dirección", "Vía de servicio para vecinos"],
     ["Поворот в эту сторону запрещён", "Служебный проезд для местных"]),
    ("paso_obligatorio", "Paso obligatorio por ese lado", "Объезд обязателен с этой стороны",
     ["Prohibido pasar por ese lado", "Carril reservado a autobuses"],
     ["Проезд с этой стороны запрещён", "Полоса только для автобусов"]),
    ("rotonda_obligatoria", "Glorieta: circular en el sentido indicado", "Круговое: ехать в указанную сторону",
     ["Cruce donde está prohibido girar a la izquierda", "Zona de maniobras para camiones"],
     ["Перекрёсток, где поворот запрещён", "Зона для манёвров грузовиков"]),
    ("via_ciclistas", "Vía obligatoria para ciclistas", "Дорожка, обязательная для велосипедистов",
     ["Prohibido el paso a bicicletas", "Aparcamiento para bicicletas"],
     ["Проезд велосипедам запрещён", "Парковка для велосипедов"]),
    ("fin_prohibiciones", "Fin de todas las prohibiciones anteriores", "Конец всех предыдущих запретов",
     ["Comienzo de una zona sin límite", "Fin de la vía asfaltada"],
     ["Начало зоны без ограничений", "Конец асфальтовой дороги"]),
    ("fin_velocidad_maxima", "Fin de esa limitación de velocidad", "Конец этого ограничения скорости",
     ["Comienzo de esa limitación", "Velocidad recomendada del tramo"],
     ["Начало этого ограничения", "Рекомендованная скорость участка"]),
    ("semaforo", "Semáforo más adelante", "Светофор впереди",
     ["Zona vigilada con cámaras", "Cruce regulado por un agente"],
     ["Зона с камерами наблюдения", "Перекрёсток с регулировщиком"]),
    ("paso_nivel_barreras", "Paso a nivel con barreras", "Железнодорожный переезд со шлагбаумом",
     ["Zona de obras con vallas", "Puente levadizo sobre el río"],
     ["Зона работ с ограждением", "Разводной мост через реку"]),
    ("paso_nivel_sin_barreras", "Paso a nivel sin barreras", "Переезд без шлагбаума",
     ["Estación de tren cercana", "Paso subterráneo para trenes"],
     ["Железнодорожная станция рядом", "Подземный переход для поездов"]),
    ("curva_derecha", "Curva peligrosa hacia la derecha", "Опасный поворот направо",
     ["Desvío obligatorio a la derecha", "Salida de vehículos por la derecha"],
     ["Обязательный объезд справа", "Выезд машин справа"]),
    ("curva_izquierda", "Curva peligrosa hacia la izquierda", "Опасный поворот налево",
     ["Desvío obligatorio a la izquierda", "Salida de vehículos por la izquierda"],
     ["Обязательный объезд слева", "Выезд машин слева"]),
    ("baden", "Resalto o badén en la calzada", "Искусственная неровность на дороге",
     ["Cambio de rasante sin visibilidad", "Paso superior para peatones"],
     ["Перелом дороги без видимости", "Надземный переход"]),
    ("estrechamiento", "Estrechamiento de la calzada", "Сужение проезжей части",
     ["Túnel estrecho sin iluminación", "Puente con carga limitada"],
     ["Узкий неосвещённый туннель", "Мост с ограничением нагрузки"]),
    ("obras", "Obras en la calzada más adelante", "Дорожные работы впереди",
     ["Fábrica junto a la carretera", "Zona de carga de materiales"],
     ["Завод рядом с дорогой", "Зона погрузки материалов"]),
    ("obras_temporal", "Obras: señal temporal que prevalece", "Работы: временный знак, он главнее",
     ["Señal informativa sin obligación", "Señal que puede ignorarse"],
     ["Информационный знак без обязанности", "Знак, который можно не выполнять"]),
    ("pavimento_deslizante", "Pavimento deslizante, poco agarre", "Скользкая дорога, плохое сцепление",
     ["Tramo con badenes seguidos", "Curva con grava en la calzada"],
     ["Участок с неровностями подряд", "Поворот с гравием на дороге"]),
    ("peatones_peligro", "Peligro por paso de peatones", "Опасность: пешеходы",
     ["Zona peatonal cerrada al tráfico", "Parada de autobús escolar"],
     ["Пешеходная зона без машин", "Остановка школьного автобуса"]),
    ("ninos", "Zona con presencia habitual de niños", "Место, где часто бывают дети",
     ["Parque infantil cerrado al tráfico", "Parada escolar de autobuses"],
     ["Детская площадка без машин", "Школьная автобусная остановка"]),
    ("ciclistas_peligro", "Paso frecuente de ciclistas", "Частое появление велосипедистов",
     ["Carril reservado a bicicletas", "Prohibición de circular en bici"],
     ["Полоса для велосипедов", "Запрет ездить на велосипеде"]),
    ("animales_sueltos", "Posible paso de animales salvajes", "Возможен выход диких животных",
     ["Granja con ganado cercana", "Reserva natural protegida"],
     ["Ферма со скотом рядом", "Охраняемый природный парк"]),
    ("otros_peligros", "Un peligro que no tiene señal propia", "Опасность, у которой нет своего знака",
     ["Avería habitual de los semáforos", "Tramo con control por radar"],
     ["Частая поломка светофоров", "Участок с камерой контроля"]),
    ("paso_peatones", "Paso de peatones: ahí tienen prioridad", "Пешеходный переход: там у них приоритет",
     ["Acera elevada sobre la calzada", "Camino reservado sólo a peatones"],
     ["Приподнятый тротуар для пешеходов", "Дорожка только для пешеходов"]),
    ("estacionamiento", "Lugar donde se permite estacionar", "Место, где стоянка разрешена",
     ["Zona de parada rápida de taxis", "Aparcamiento exclusivo de policía"],
     ["Зона быстрой остановки такси", "Парковка только для полиции"]),
    ("calle_residencial", "Calle residencial: el peatón manda", "Жилая зона: пешеход главнее",
     ["Zona de viviendas sin salida", "Aparcamiento sólo para vecinos"],
     ["Жилой квартал без выезда", "Парковка только для местных"]),
    ("marca_continua", "No puede rebasarse ni pisarse", "Её нельзя ни пересекать, ни наезжать",
     ["Puede rebasarse para adelantar", "Sólo separa los sentidos, sin prohibir"],
     ["Можно пересекать для обгона", "Просто разделяет потоки, не запрещая"]),
    ("marca_doble", "No puede rebasarse en ningún sentido", "Нельзя пересекать ни в одну сторону",
     ["Puede rebasarla quien adelanta", "Sólo separa los sentidos, sin prohibir"],
     ["Может пересечь обгоняющий", "Просто разделяет потоки, не запрещая"]),
    ("marca_discontinua", "Puede rebasarse para adelantar o cambiar de carril",
     "Можно пересекать для обгона и смены полосы",
     ["No puede rebasarse ni pisarse en ningún caso", "Sólo pueden rebasarla motos y bicicletas"],
     ["Нельзя пересекать ни при каких условиях", "Пересекать могут только мотоциклы"]),
    ("marca_zigzag", "Prohibido estacionar junto al bordillo", "Стоянка у бордюра запрещена",
     ["Zona de carga y descarga", "Aparcamiento libre para residentes"],
     ["Зона погрузки и разгрузки", "Свободная парковка для местных"]),
    ("semaforo_ambar", "Detenerse, salvo que frenar sea peligroso", "Остановиться, если торможение не опасно",
     ["Acelerar para pasar antes del rojo", "Seguir adelante sin obligación"],
     ["Ускориться и проскочить до красного", "Ехать дальше без обязательств"]),
    ("semaforo_ambar_intermitente", "Pasar con precaución: rige la señalización",
     "Ехать осторожно: действуют знаки",
     ["Detenerse por completo y esperar el verde", "Que el semáforo está averiado del todo"],
     ["Полностью остановиться и ждать", "Что светофор сломан"]),
]

# ⚠️ Две формулировки на знак, а не три. Третья ничего не добавляла: варианты
# ответа те же, отличалась только шапка вопроса — человек видел один и тот же знак
# трижды подряд и злился. Объём должен идти от новых правил, а не от переформулировок.
PLANTILLAS_SENAL = [
    ("¿Qué significa esta señal?", "Что означает этот знак?"),
    ("Al ver esta señal sabes que:", "Увидев этот знак, ты знаешь, что:"),
]


def preguntas_senales():
    salida = []
    for clave, bien_es, bien_ru, mal_es, mal_ru in SIGNIFICADOS:
        for es, ru in PLANTILLAS_SENAL:
            salida.append({
                "t": "senales", "s": clave, "q": es, "q_ru": ru,
                "o": [bien_es] + mal_es, "o_ru": [bien_ru] + mal_ru,
                "e": bien_ru + ".",
            })
    return salida


def escribir(preguntas):
    def js(v):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'

    lineas = ['/* Вопросы, собранные из таблиц правил: `python generar-preguntas.py`.',
              '',
              '   ⚠️ РУКАМИ НЕ ПРАВИТЬ — перезапишется при следующей сборке. Правило живёт',
              '   в таблице внутри generar-preguntas.py; ошиблись в правиле — поправили в одном',
              '   месте, и оно разъехалось по всем вопросам разом.',
              '',
              '   Рукописные вопросы (на понимание, на ситуацию) лежат отдельно, в preguntas.js,',
              '   и генератор их не трогает. Оба банка складываются в браузере. */',
              '',
              'const PREGUNTAS_AUTO = [']
    for p in preguntas:
        campos = ['t:' + js(p["t"])]
        if p.get("s"):
            campos.append('s:' + js(p["s"]))
        campos += ['q:' + js(p["q"]), 'q_ru:' + js(p["q_ru"])]
        linea = '{' + ', '.join(campos) + ','
        lineas.append(linea)
        lineas.append(' o:[' + ','.join(js(x) for x in p["o"]) + '],'
                      ' o_ru:[' + ','.join(js(x) for x in p["o_ru"]) + '], a:0,')
        lineas.append(' e:' + js(p["e"]) + '},')
    lineas.append('];')
    lineas.append('if (typeof module !== "undefined") module.exports = PREGUNTAS_AUTO;')
    io.open("preguntas-auto.js", "w", encoding="utf-8").write("\n".join(lineas) + "\n")


def ya_escritas_a_mano():
    """Пары «знак + правильный ответ», которые уже есть в рукописном банке.

    ⚠️ Без этого генератор плодит близнецов: тот же знак, тот же верный ответ,
    отличается только шапка вопроса. Тридцать восемь таких он и сделал на первом
    прогоне — выбрасываем их, рукописный вариант всегда точнее.
    """
    try:
        r = subprocess.run(
            ["node", "-e",
             'const P=require("./preguntas.js");'
             'console.log(JSON.stringify(P.filter(p=>p.s).map(p=>p.s+"|"+p.o[p.a])))'],
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        return set(json.loads(r.stdout))
    except Exception as e:
        print("рукописный банк не прочитался:", e)
        return set()


def revisar_longitudes(preguntas):
    """Правильный ответ не должен быть заметно длиннее неверных.

    ⚠️ Это та же проверка, что в auditoria.js, только раньше по времени: аудит
    ловит уже собранный банк, а тут видно, какая СТРОКА ТАБЛИЦЫ виновата.
    Порог 1,2 — как в аудите, чтобы два прибора не спорили.
    """
    malas = []
    for p in preguntas:
        largos = [len(o) for o in p["o"]]
        if len(largos) < 2:
            continue
        ventaja = largos[0] / max(largos[1:])
        if ventaja >= 1.2:
            malas.append((ventaja, p.get("s") or p["t"], p["o"][0]))
    for v, quien, texto in sorted(malas, reverse=True):
        print("  ⚠️ %-28s правильный длиннее в %.2f раза — %s" % (quien, v, texto))
    return len(malas)


def main():
    partes = [("скорость", preguntas_velocidad()),
              ("баллы", preguntas_puntos()),
              ("знаки", preguntas_senales())]
    conocidas = ya_escritas_a_mano()
    todas, saltadas = [], 0
    for nombre, lote in partes:
        limpio = []
        for p in lote:
            if p.get("s") and (p["s"] + "|" + p["o"][0]) in conocidas:
                saltadas += 1
                continue
            limpio.append(p)
        print("%-10s %4d вопросов" % (nombre, len(limpio)))
        todas += limpio
    if saltadas:
        print("пропущено близнецов рукописных:", saltadas)
    problemas = revisar_longitudes(todas)
    escribir(todas)
    print("---")
    print("собрано в preguntas-auto.js:", len(todas),
          "| перекосов по длине:", problemas)


if __name__ == "__main__":
    main()
