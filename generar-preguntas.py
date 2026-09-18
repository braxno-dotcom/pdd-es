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



# ============================ РЕАКЦИЯ И ПУТЬ ============================
# ⚠️ Это НЕ правило, а арифметика: за секунду машина проезжает скорость/3,6 метра.
# Потому и безопасно генерировать: тут нечему устареть и не в чем ошибиться.
# Секунда — типичное время реакции, его и используют в автошколах.
VELOCIDADES_REACCION = [30, 50, 80, 90, 100, 120]


def preguntas_reaccion():
    salida = []
    for v in VELOCIDADES_REACCION:
        metros = round(v / 3.6)
        malos = sorted({round(metros * 0.6), round(metros * 1.5)} - {metros})[:2]
        salida.append({
            "t": "seguridad",
            "q": "A %d km/h, ¿cuántos metros recorre el coche en un segundo de reacción?" % v,
            "q_ru": "На скорости %d км/ч сколько метров машина проезжает за секунду реакции?" % v,
            "o": ["Unos %d metros" % metros] + ["Unos %d metros" % m for m in malos],
            "o_ru": ["Около %d метров" % metros] + ["Около %d метров" % m for m in malos],
            "e": "Скорость делить на 3,6 — это метры за секунду: %d км/ч дают %d м." % (v, metros),
        })
    return salida


# ============================ АЛКОГОЛЬ ============================
# Норма в выдыхаемом воздухе и в крови, по типу водителя.
TASAS = [
    ("un conductor con más de dos años de permiso", "водителя со стажем больше двух лет", "0,25", "0,5"),
    ("un conductor novel (menos de dos años)", "начинающего водителя (меньше двух лет)", "0,15", "0,3"),
    ("un conductor profesional", "профессионального водителя", "0,15", "0,3"),
    ("un conductor de autobús escolar", "водителя школьного автобуса", "0,15", "0,3"),
    ("un ciclista", "велосипедиста", "0,25", "0,5"),
]


def preguntas_alcohol():
    salida = []
    otros_aire = ["0,15", "0,25", "0,30", "0,50"]
    otros_sangre = ["0,3", "0,5", "0,8", "1,0"]
    for quien_es, quien_ru, aire, sangre in TASAS:
        malos_a = [x for x in otros_aire if x != aire][:2]
        malos_s = [x for x in otros_sangre if x != sangre][:2]
        salida.append({
            "t": "alcohol",
            "q": "¿Cuál es la tasa máxima de alcohol en aire espirado para %s?" % quien_es,
            "q_ru": "Какова максимальная норма алкоголя в выдыхаемом воздухе для %s?" % quien_ru,
            "o": ["%s mg/l" % aire] + ["%s mg/l" % m for m in malos_a],
            "o_ru": ["%s мг/л" % aire] + ["%s мг/л" % m for m in malos_a],
            "e": "Для %s норма в воздухе — %s мг/л." % (quien_ru, aire),
        })
        salida.append({
            "t": "alcohol",
            "q": "¿Cuál es la tasa máxima de alcohol en sangre para %s?" % quien_es,
            "q_ru": "Какова максимальная норма алкоголя в крови для %s?" % quien_ru,
            "o": ["%s g/l" % sangre] + ["%s g/l" % m for m in malos_s],
            "o_ru": ["%s г/л" % sangre] + ["%s г/л" % m for m in malos_s],
            "e": "Для %s норма в крови — %s г/л." % (quien_ru, sangre),
        })
    return salida


# ============================ КАТЕГОРИИ ПРАВ ============================
# Возраст и что разрешает. Правило записано один раз.
PERMISOS = [
    ("AM", "15", "ciclomotores de hasta 45 km/h", "мопеды до 45 км/ч"),
    ("A1", "16", "motos ligeras de hasta 125 cc", "лёгкие мотоциклы до 125 кубиков"),
    ("A2", "18", "motos de potencia media limitada", "мотоциклы средней мощности"),
    ("B", "18", "turismos de hasta 3.500 kg", "легковые до 3500 кг"),
]


def preguntas_permisos():
    salida = []
    edades = ["14", "15", "16", "18", "21"]
    for cat, edad, que_es, que_ru in PERMISOS:
        malas = [e for e in edades if e != edad][:2]
        salida.append({
            "t": "documentos",
            "q": "¿A partir de qué edad se puede obtener el permiso %s?" % cat,
            "q_ru": "С какого возраста можно получить категорию %s?" % cat,
            "o": ["%s años" % edad] + ["%s años" % m for m in malas],
            "o_ru": ["%s лет" % edad] + ["%s лет" % m for m in malas],
            "e": "Категория %s — с %s лет (%s)." % (cat, edad, que_ru),
        })
        otros = [q for c, e, q, r in PERMISOS if c != cat][:2]
        salida.append({
            "t": "documentos",
            "q": "¿Qué permite conducir el permiso %s?" % cat,
            "q_ru": "Что разрешает категория %s?" % cat,
            "o": [que_es.capitalize()] + [o.capitalize() for o in otros],
            "o_ru": [que_ru.capitalize()] + [r.capitalize() for c, e, q, r in PERMISOS if c != cat][:2],
            "e": "Категория %s — это %s." % (cat, que_ru),
        })
    return salida


# ============================ СРОКИ ============================
# Всё, что меряется временем: годность, продление, техосмотр, обжалование.
PLAZOS = [
    ("la validez del examen teórico aprobado", "годность сданной теории", "Dos años", "Два года",
     ["Seis meses", "Cinco años"], ["Полгода", "Пять лет"]),
    ("la renovación del permiso B antes de los 65 años", "продление категории B до 65 лет",
     "Cada diez años", "Каждые десять лет", ["Cada cinco años", "Cada quince años"],
     ["Каждые пять лет", "Каждые пятнадцать лет"]),
    ("la renovación del permiso B después de los 65 años", "продление категории B после 65 лет",
     "Cada cinco años", "Каждые пять лет", ["Cada diez años", "Cada dos años"],
     ["Каждые десять лет", "Каждые два года"]),
    ("la ITV de un turismo de cuatro a diez años", "техосмотр легковой машины 4-10 лет",
     "Cada dos años", "Каждые два года", ["Cada año", "Cada cuatro años"],
     ["Ежегодно", "Каждые четыре года"]),
    ("la ITV de un turismo de más de diez años", "техосмотр легковой машины старше десяти лет",
     "Cada año", "Ежегодно", ["Cada dos años", "Cada seis meses"],
     ["Каждые два года", "Каждые полгода"]),
    ("el plazo para pagar una multa con descuento", "срок оплаты штрафа со скидкой",
     "Veinte días naturales", "Двадцать календарных дней", ["Diez días naturales", "Dos meses"],
     ["Десять календарных дней", "Два месяца"]),
    ("el plazo para recurrir una multa", "срок обжалования штрафа",
     "Veinte días naturales", "Двадцать календарных дней", ["Cinco días naturales", "Tres meses"],
     ["Пять календарных дней", "Три месяца"]),
    ("el tiempo sin infracciones graves para recuperar todos los puntos",
     "срок без серьёзных нарушений для возврата всех баллов",
     "Dos años", "Два года", ["Seis meses", "Cuatro años"], ["Полгода", "Четыре года"]),
    ("la duración del curso de recuperación parcial de puntos",
     "длительность курса частичного восстановления баллов",
     "Doce horas", "Двенадцать часов", ["Cuatro horas", "Veinticuatro horas"],
     ["Четыре часа", "Двадцать четыре часа"]),
    ("el plazo para hacer el examen práctico tras aprobar el teórico",
     "срок сдачи практики после теории",
     "Dos años", "Два года", ["Seis meses", "Un año"], ["Полгода", "Один год"]),
]


def preguntas_plazos():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in PLAZOS:
        salida.append({
            "t": "documentos",
            "q": "¿Cuál es %s?" % es,
            "q_ru": "Каков %s?" % ru if ru.startswith("срок") else "Какова периодичность: %s?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s — %s." % (ru.capitalize(), bien_ru.lower()),
        })
    return salida


# ============================ ОГНИ ============================
LUCES = [
    ("con niebla densa de día", "в густом тумане днём",
     "Luz de niebla y luz de cruce", "Противотуманные и ближний свет",
     ["Luz de carretera y de posición", "Sólo las luces de posición"],
     ["Дальний и габариты", "Только габариты"]),
    ("al circular por un túnel iluminado", "при проезде освещённого туннеля",
     "Luz de cruce encendida", "Включённый ближний свет",
     ["Sólo las luces de posición", "Luz de carretera encendida"],
     ["Только габариты", "Включённый дальний свет"]),
    ("al cruzarse con otro vehículo de noche", "при встрече с машиной ночью",
     "Cambiar a luz de cruce", "Переключиться на ближний",
     ["Mantener la luz de carretera", "Apagar todas las luces"],
     ["Оставить дальний", "Выключить весь свет"]),
    ("al detenerse en el arcén de noche", "при остановке на обочине ночью",
     "Luces de posición y emergencia", "Габариты и аварийка",
     ["Luz de carretera encendida", "Todas las luces apagadas"],
     ["Включённый дальний", "Весь свет выключен"]),
]


def preguntas_luces():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in LUCES:
        salida.append({
            "t": "seguridad",
            "q": "¿Qué luces se utilizan %s?" % es,
            "q_ru": "Какой свет включают %s?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s: %s." % (ru.capitalize(), bien_ru.lower()),
        })
    return salida


# ============================ ШТРАФЫ В ЕВРО ============================
IMPORTES = [
    ("una infracción leve", "лёгкое нарушение", "100"),
    ("una infracción grave", "серьёзное нарушение", "200"),
    ("una infracción muy grave", "особо тяжкое нарушение", "500"),
]


def preguntas_importes():
    salida = []
    todos = ["100", "200", "500"]
    for es, ru, importe in IMPORTES:
        malos = [x for x in todos if x != importe]
        salida.append({
            "t": "multas",
            "q": "¿Cuál es el importe habitual de %s?" % es,
            "q_ru": "Каков обычный размер штрафа за %s?" % ru,
            "o": ["%s euros" % importe] + ["%s euros" % m for m in malos],
            "o_ru": ["%s евро" % importe] + ["%s евро" % m for m in malos],
            "e": "%s — %s евро." % (ru.capitalize(), importe),
        })
    return salida



# ============================ ПРИОРИТЕТ ============================
# Кто кого пропускает. Ситуация записана один раз, вопросов из неё два.
PRIORIDAD = [
    ("en una glorieta", "на круговом движении",
     "Ceden los que entran en ella", "Уступают те, кто въезжает",
     ["Ceden los que ya circulan dentro", "Cede siempre el vehículo más lento"],
     ["Уступают те, кто уже внутри", "Уступает самая медленная машина"]),
    ("en un cruce sin señales", "на перекрёстке без знаков",
     "Cede quien tiene un vehículo a su derecha", "Уступает тот, у кого машина справа",
     ["Cede quien circula en línea recta hacia el cruce", "Cede el vehículo de menor tamaño"],
     ["Уступает тот, кто едет прямо", "Уступает машина поменьше"]),
    ("al salir de un aparcamiento", "при выезде с парковки",
     "Cede el que sale a todos los demás", "Выезжающий уступает всем",
     ["Ceden los que circulan por la vía", "Pasa primero quien llegue antes"],
     ["Уступают те, кто едет по дороге", "Первым едет подъехавший раньше"]),
    ("ante un vehículo de emergencia con sirena", "перед спецтранспортом с сиреной",
     "Todos le facilitan el paso", "Все освобождают ему дорогу",
     ["Sólo ceden los que van detrás", "Nadie está obligado a cederle"],
     ["Уступают только едущие сзади", "Никто не обязан уступать"]),
    ("ante un tranvía en la calzada", "перед трамваем на проезжей части",
     "El tranvía pasa primero siempre", "Трамвай проезжает первым всегда",
     ["El tranvía cede en los cruces", "Pasa primero quien llegue antes"],
     ["Трамвай уступает на перекрёстках", "Первым едет подъехавший раньше"]),
    ("al incorporarse por un carril de aceleración", "при выезде по полосе разгона",
     "Cede quien se incorpora a la vía", "Уступает тот, кто вливается",
     ["Ceden los que ya van por la vía", "Pasa primero el más rápido"],
     ["Уступают те, кто уже едет", "Первым едет самый быстрый"]),
    ("al hacer un cambio de sentido", "при развороте",
     "Cede a todos, vengan de donde vengan", "Уступает всем, откуда бы ни ехали",
     ["Sólo cede a los que vienen de frente", "Tiene preferencia por ser maniobra"],
     ["Уступает только встречным", "Имеет приоритет как манёвр"]),
    ("al circular marcha atrás", "при движении задним ходом",
     "Cede el paso a todos los demás", "Уступает всем остальным",
     ["Mantiene la preferencia que tenía", "Tiene preferencia sobre los peatones"],
     ["Сохраняет прежний приоритет", "Имеет приоритет над пешеходами"]),
    ("ante un autobús que sale de su parada en ciudad", "перед автобусом от остановки в городе",
     "Se le cede el paso al autobús", "Автобусу уступают дорогу",
     ["El autobús cede a todo el mundo", "Pasa primero quien llegue antes"],
     ["Автобус уступает всем", "Первым едет подъехавший раньше"]),
    ("en una pendiente estrecha", "на узком подъёме",
     "Cede quien baja la pendiente", "Уступает едущий вниз",
     ["Cede quien sube la pendiente", "Cede el vehículo más pesado"],
     ["Уступает едущий вверх", "Уступает более тяжёлая машина"]),
    ("ante un peatón en un paso sin semáforo", "перед пешеходом на зебре без светофора",
     "El peatón tiene prioridad siempre", "Пешеход имеет приоритет всегда",
     ["El peatón espera a que pase el coche", "El peatón sólo tiene prioridad de día"],
     ["Пешеход ждёт, пока проедет машина", "Пешеход главнее только днём"]),
    ("al girar cruzando un carril bici", "при повороте через велополосу",
     "Cede el paso a los ciclistas", "Уступает велосипедистам",
     ["Los ciclistas ceden al coche", "Pasa primero quien llegue antes"],
     ["Велосипедисты уступают машине", "Первым едет подъехавший раньше"]),
]

PLANTILLAS_PRIORIDAD = [
    ("¿Quién cede el paso {donde}?", "Кто уступает дорогу {donde_ru}?"),
    ("La prioridad {donde} funciona así:", "Приоритет {donde_ru} работает так:"),
]


def preguntas_prioridad():
    salida = []
    for donde_es, donde_ru, bien_es, bien_ru, mal_es, mal_ru in PRIORIDAD:
        for es, ru in PLANTILLAS_PRIORIDAD:
            salida.append({
                "t": "prioridad",
                "q": es.format(donde=donde_es),
                "q_ru": ru.format(donde_ru=donde_ru),
                "o": [bien_es] + mal_es,
                "o_ru": [bien_ru] + mal_ru,
                "e": "%s: %s." % (donde_ru.capitalize(), bien_ru.lower()),
            })
    return salida


# ============================ БЕЗОПАСНОСТЬ ============================
SEGURIDAD = [
    ("el cinturón de seguridad", "ремень безопасности",
     "Obligatorio en todas las plazas", "Обязателен на всех местах",
     ["Obligatorio sólo delante", "Obligatorio sólo fuera de ciudad"],
     ["Обязателен только спереди", "Обязателен только за городом"]),
    ("el casco en moto", "шлем на мотоцикле",
     "Obligatorio siempre, también en ciudad", "Обязателен всегда, и в городе тоже",
     ["Obligatorio sólo fuera de poblado", "Obligatorio sólo en autovía"],
     ["Обязателен только за городом", "Обязателен только на магистрали"]),
    ("la baliza V-16", "маячок V-16",
     "Sustituye a los triángulos desde 2026", "Заменяет треугольники с 2026 года",
     ["Se usa junto con los triángulos", "Sólo es obligatoria de noche"],
     ["Используется вместе с треугольниками", "Обязателен только ночью"]),
    ("el chaleco reflectante", "светоотражающий жилет",
     "Se pone antes de salir del coche", "Надевают до выхода из машины",
     ["Se pone una vez fuera del coche", "Sólo hace falta de noche"],
     ["Надевают уже снаружи", "Нужен только ночью"]),
    ("la silla infantil hasta 135 cm", "детское кресло до 135 см",
     "Obligatoria y en los asientos traseros", "Обязательно, и на задних сиденьях",
     ["Obligatoria sólo en viajes largos", "Basta con el cinturón del coche"],
     ["Обязательно только в дальних поездках", "Хватает обычного ремня"]),
    ("la silla a contramarcha delante", "кресло против хода на переднем сиденье",
     "Exige desactivar el airbag frontal", "Требует отключить подушку",
     ["Exige retrasar el asiento del todo", "Está prohibida en cualquier caso"],
     ["Требует отодвинуть сиденье назад", "Запрещено в любом случае"]),
    ("el extintor en un turismo particular", "огнетушитель в личной легковой",
     "No es obligatorio llevarlo", "Возить необязательно",
     ["Es obligatorio desde hace años", "Es obligatorio sólo en verano"],
     ["Обязателен уже много лет", "Обязателен только летом"]),
    ("la profundidad del dibujo del neumático", "глубина протектора шины",
     "Mínimo un milímetro y seis", "Минимум полтора миллиметра с лишним",
     ["Mínimo dos milímetros y medio", "Mínimo un milímetro justo"],
     ["Минимум два с половиной миллиметра", "Минимум ровно один миллиметр"]),
    ("la presión de los neumáticos", "давление в шинах",
     "Se mide en frío, una vez al mes", "Меряют на холодных, раз в месяц",
     ["Se mide en caliente tras rodar", "Se mide una vez al año en la ITV"],
     ["Меряют на горячих после езды", "Меряют раз в год на техосмотре"]),
    ("los auriculares conectados al móvil", "наушники, подключённые к телефону",
     "Están prohibidos al conducir", "Запрещены за рулём",
     ["Se permiten fuera de ciudad", "Se permiten con manos libres"],
     ["Разрешены за городом", "Разрешены при свободных руках"]),
]


def preguntas_seguridad_tabla():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in SEGURIDAD:
        salida.append({
            "t": "seguridad",
            "q": "¿Qué norma rige para %s?" % es,
            "q_ru": "Какое правило действует для «%s»?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s: %s." % (ru.capitalize(), bien_ru.lower()),
        })
    return salida


# ============================ ЧТО ВОЗИТЬ И ЭКОЛОГИЯ ============================
DOCUMENTOS_TABLA = [
    ("el permiso de conducir", "водительские права",
     "Siempre encima al conducir", "Всегда с собой за рулём",
     ["Sólo en los viajes largos", "Basta una foto en el móvil"],
     ["Только в дальних поездках", "Хватает фото в телефоне"]),
    ("el permiso de circulación", "свидетельство о регистрации",
     "Documento obligatorio del vehículo", "Обязательный документ на машину",
     ["Documento opcional, no siempre exigido", "Sólo hace falta para vender el coche"],
     ["Необязательный документ", "Нужен только для продажи"]),
    ("la ficha técnica", "техпаспорт с отметками ITV",
     "Documento obligatorio del vehículo", "Обязательный документ на машину",
     ["Sólo hace falta el día de la ITV", "Sólo hace falta para vender el coche"],
     ["Нужен только на техосмотре", "Нужен только для продажи"]),
    ("el seguro obligatorio", "обязательная страховка",
     "Cubre los daños a terceros", "Покрывает ущерб третьим лицам",
     ["Cubre todos los daños propios", "Cubre sólo al conductor"],
     ["Покрывает свой ущерб полностью", "Покрывает только водителя"]),
    ("el distintivo ambiental", "экологическая наклейка",
     "Clasifica el coche por emisiones", "Делит машины по выбросам",
     ["Clasifica el coche por antigüedad", "Clasifica el coche por potencia"],
     ["Делит машины по возрасту", "Делит машины по мощности"]),
    ("la Zona de Bajas Emisiones", "зона низких выбросов",
     "Obligatoria en ciudades grandes", "Обязательна в крупных городах",
     ["Existe sólo en la capital", "Funciona sólo los fines de semana"],
     ["Есть только в столице", "Работает только по выходным"]),
]


def preguntas_documentos_tabla():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in DOCUMENTOS_TABLA:
        salida.append({
            "t": "documentos",
            "q": "¿Qué hay que saber sobre %s?" % es,
            "q_ru": "Что нужно знать про «%s»?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s: %s." % (ru.capitalize(), bien_ru.lower()),
        })
    return salida



# ============================ ГДЕ НЕЛЬЗЯ СТОЯТЬ ============================
# Список мест, где стоянка или остановка запрещены. Ответ один и тот же по смыслу,
# поэтому меняем не ответ, а МЕСТО — так вопросы остаются разными.
SIN_ESTACIONAR = [
    ("sobre un paso de peatones", "на пешеходном переходе"),
    ("sobre un carril bici", "на велосипедной дорожке"),
    ("sobre la acera", "на тротуаре"),
    ("en una parada de autobús", "на автобусной остановке"),
    ("delante de un vado señalizado", "перед обозначенным выездом"),
    ("en doble fila", "вторым рядом"),
    ("dentro de una intersección", "прямо на перекрёстке"),
    ("en un túnel o bajo un puente", "в туннеле или под мостом"),
    ("en una plaza para personas con discapacidad sin tarjeta",
     "на месте для людей с инвалидностью без карточки"),
    ("en un carril reservado al transporte público", "на полосе общественного транспорта"),
]


def preguntas_estacionar():
    salida = []
    for es, ru in SIN_ESTACIONAR:
        salida.append({
            "t": "multas",
            "q": "Estacionar %s:" % es,
            "q_ru": "Стоянка %s:" % ru,
            "o": ["Está prohibido y se sanciona",
                  "Se permite durante unos minutos",
                  "Se permite si no molesta a nadie"],
            "o_ru": ["Запрещена и наказуема",
                     "Разрешена на несколько минут",
                     "Разрешена, если никому не мешает"],
            "e": "Стоянка %s запрещена: за это штрафуют и могут увезти машину." % ru,
        })
    return salida


# ============================ ГДЕ НЕЛЬЗЯ ОБГОНЯТЬ ============================
SIN_ADELANTAR = [
    ("en un cambio de rasante sin visibilidad", "на переломе дороги без видимости"),
    ("en una curva de visibilidad reducida", "на повороте с плохой видимостью"),
    ("en un paso a nivel y en sus proximidades", "на переезде и рядом с ним"),
    ("justo antes de un paso de peatones", "прямо перед пешеходным переходом"),
    ("donde la marca vial es una línea continua", "там, где разметка сплошная"),
    ("en un túnel de un solo carril por sentido", "в туннеле с одной полосой в сторону"),
]


def preguntas_adelantar():
    salida = []
    for es, ru in SIN_ADELANTAR:
        salida.append({
            "t": "prioridad",
            "q": "Adelantar %s:" % es,
            "q_ru": "Обгон %s:" % ru,
            "o": ["Está prohibido en todo caso",
                  "Se permite si no viene nadie",
                  "Se permite a poca velocidad"],
            "o_ru": ["Запрещён в любом случае",
                     "Разрешён, если никто не едет навстречу",
                     "Разрешён на малой скорости"],
            "e": "Обгон %s запрещён — видимости или места для манёвра там нет." % ru,
        })
    return salida


# ============================ МАНЁВРЫ И СИГНАЛЫ ============================
MANIOBRAS = [
    ("al cambiar de carril", "при смене полосы",
     "Señalizar con el intermitente antes", "Заранее включить поворотник",
     ["Basta con mirar por el retrovisor", "Basta con hacerlo despacio"],
     ["Достаточно посмотреть в зеркало", "Достаточно сделать это медленно"]),
    ("al salir de una glorieta", "при съезде с кругового",
     "Señalizar a la derecha antes de salir", "Показать направо перед съездом",
     ["No hace falta señalizar nada", "Señalizar a la izquierda al salir"],
     ["Показывать ничего не нужно", "Показать налево при съезде"]),
    ("al incorporarse desde un estacionamiento", "при выезде со стоянки",
     "Señalizar y ceder el paso a todos", "Показать поворот и уступить всем",
     ["Señalizar basta, la prioridad es tuya", "Tocar el claxon para avisar"],
     ["Достаточно показать поворот, приоритет твой", "Посигналить, чтобы предупредить"]),
    ("con las luces de emergencia", "с аварийной сигнализацией",
     "Avisar de una retención o un peligro", "Предупредить о заторе или опасности",
     ["Aparcar un momento en doble fila", "Circular más despacio de lo normal"],
     ["Постоять минуту вторым рядом", "Ехать медленнее обычного"]),
    ("con el claxon en ciudad", "с клаксоном в городе",
     "Sólo para evitar un peligro inmediato", "Только чтобы избежать опасности",
     ["Para avisar de que vas a adelantar", "Para meter prisa al de delante"],
     ["Чтобы предупредить об обгоне", "Чтобы поторопить переднего"]),
    ("al girar a la izquierda en un cruce", "при повороте налево на перекрёстке",
     "Ceder el paso a los que vienen de frente", "Уступить встречным",
     ["Pasar primero, ya que eres el que gira", "Tocar el claxon y girar sin más"],
     ["Проехать первым, раз поворачиваешь", "Посигналить и повернуть"]),
    ("antes de abrir la puerta al aparcar", "перед открытием двери на парковке",
     "Mirar atrás por ciclistas y coches", "Посмотреть назад: велосипеды и машины",
     ["Abrir despacio es suficiente", "No hace falta mirar si está parado"],
     ["Достаточно открыть медленно", "Смотреть не нужно, машина стоит"]),
    ("al circular detrás de una ambulancia con sirena", "при движении за скорой с сиреной",
     "Facilitarle el paso y no seguirla de cerca", "Освободить дорогу и не ехать вплотную",
     ["Seguirla de cerca para avanzar antes", "Adelantarla si va despacio"],
     ["Ехать вплотную, чтобы продвинуться", "Обогнать, если едет медленно"]),
]


def preguntas_maniobras():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in MANIOBRAS:
        salida.append({
            "t": "seguridad",
            "q": "¿Qué hay que hacer %s?" % es,
            "q_ru": "Что нужно делать %s?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s: %s." % (ru.capitalize(), bien_ru.lower()),
        })
    return salida


# ============================ АВАРИЯ: ПРАВИЛО PAS ============================
# Proteger, Avisar, Socorrer — защитить, вызвать, помочь. Этому учат везде.
ACCIDENTE = [
    ("lo primero que se hace al llegar a un accidente", "первое, что делают на месте аварии",
     "Proteger el lugar para evitar otro choque", "Защитить место, чтобы не было второй аварии",
     ["Mover a los heridos fuera de los coches", "Fotografiar todo para el seguro"],
     ["Вытащить пострадавших из машин", "Сфотографировать всё для страховой"]),
    ("el número de emergencias en España", "номер экстренных служб в Испании",
     "El 112, gratuito desde cualquier móvil", "112, бесплатно с любого телефона",
     ["El 080 de los bomberos", "El 060 de información administrativa"],
     ["080, пожарные", "060, справочная администрации"]),
    ("qué NO se debe hacer con un motorista caído", "чего НЕ делать с упавшим мотоциклистом",
     "No quitarle el casco salvo peligro vital", "Не снимать шлем без угрозы жизни",
     ["Quitarle el casco siempre y rápido", "Sentarlo para que respire mejor"],
     ["Снять шлем сразу и быстро", "Усадить, чтобы легче дышал"]),
    ("cómo se señaliza el vehículo accidentado desde 2026",
     "как обозначают аварийную машину с 2026 года",
     "Con la baliza V-16 conectada", "Светящимся маячком V-16",
     ["Con los dos triángulos de siempre", "Con las luces de carretera encendidas"],
     ["Двумя привычными треугольниками", "Включённым дальним светом"]),
    ("qué hacer si hay heridos y no sabes primeros auxilios",
     "что делать при пострадавших, если не умеешь оказывать помощь",
     "Llamar al 112 y seguir sus instrucciones", "Позвонить 112 и слушать указания",
     ["Esperar a que llegue alguien que sepa", "Llevar al herido al hospital en tu coche"],
     ["Ждать того, кто умеет", "Везти пострадавшего в больницу самому"]),
    ("el parte amistoso de accidente", "европротокол о ДТП",
     "Se rellena y firma entre los implicados", "Заполняют и подписывают участники",
     ["Lo rellena siempre la policía local", "Sólo vale si hay heridos graves"],
     ["Заполняет всегда полиция", "Годится только при пострадавших"]),
]


def preguntas_accidente():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in ACCIDENTE:
        salida.append({
            "t": "seguridad",
            "q": "¿Cuál es %s?" % es if es.startswith(("el ", "lo ")) else "¿Sabes %s?" % es,
            "q_ru": "Знаешь, %s?" % ru if not ru.startswith(("первое", "номер", "как", "что")) else "%s?" % ru.capitalize(),
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": bien_ru + ".",
        })
    return salida


# ============================ СОСТОЯНИЕ ВОДИТЕЛЯ ============================
CONDUCTOR = [
    ("la somnolencia al volante", "сонливость за рулём",
     "Se combate parando a descansar", "Лечится остановкой и отдыхом",
     ["Se combate con música alta", "Se combate abriendo la ventanilla"],
     ["Лечится громкой музыкой", "Лечится открытым окном"]),
    ("conducir con gafas graduadas obligatorias", "езда в обязательных очках",
     "Figura como condición en el permiso", "Отмечено условием в правах",
     ["Es una recomendación del médico", "Sólo hace falta de noche"],
     ["Это рекомендация врача", "Нужны только ночью"]),
    ("un viaje largo por autopista", "долгая поездка по магистрали",
     "Conviene parar cada dos horas", "Стоит останавливаться каждые два часа",
     ["Conviene no parar para llegar antes", "Basta con parar al repostar"],
     ["Лучше не останавливаться, чтобы успеть", "Хватает остановки на заправке"]),
    ("el estrés y la prisa al conducir", "спешка и стресс за рулём",
     "Aumentan los errores y los riesgos", "Увеличивают число ошибок и риск",
     ["Mejoran la concentración al volante", "No influyen si se conoce la ruta"],
     ["Улучшают собранность за рулём", "Не влияют, если дорога знакома"]),
    ("comer copiosamente antes de conducir", "плотно поесть перед поездкой",
     "Favorece la somnolencia al volante", "Усиливает сонливость за рулём",
     ["No tiene ningún efecto al volante", "Mejora la atención por la energía"],
     ["Никак не влияет за рулём", "Улучшает внимание за счёт энергии"]),
    ("conducir con fiebre o dolor fuerte", "езда с температурой или сильной болью",
     "Reduce la atención y conviene evitarlo", "Снижает внимание, лучше не садиться",
     ["No afecta si el trayecto es corto", "Se compensa conduciendo más despacio"],
     ["Не мешает, если ехать недалеко", "Компенсируется медленной ездой"]),
]


def preguntas_conductor():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in CONDUCTOR:
        salida.append({
            "t": "alcohol",
            "q": "¿Qué se sabe sobre %s?" % es,
            "q_ru": "Что известно про «%s»?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s: %s." % (ru.capitalize(), bien_ru.lower()),
        })
    return salida


# ============================ ГРУЗ И ПАССАЖИРЫ ============================
CARGA = [
    ("una carga que sobresale por detrás", "груз, выступающий сзади",
     "Se señaliza con el panel V-20", "Обозначается щитком V-20",
     ["Se señaliza con un trapo rojo", "Se señaliza con las luces de emergencia"],
     ["Обозначается красной тряпкой", "Обозначается аварийной сигнализацией"]),
    ("llevar pasajeros en la zona de carga", "перевозка людей в грузовом отсеке",
     "Está prohibido en cualquier caso", "Запрещена в любом случае",
     ["Se permite en trayectos cortos", "Se permite fuera de ciudad"],
     ["Разрешена на коротких поездках", "Разрешена за городом"]),
    ("el número de pasajeros permitido", "число пассажиров",
     "El que indica la ficha técnica", "То, что указано в техпаспорте",
     ["Los que quepan con cinturón", "Uno más si es un niño"],
     ["Сколько влезет с ремнями", "На одного больше, если это ребёнок"]),
    ("una carga mal sujeta", "плохо закреплённый груз",
     "Es infracción y peligro para otros", "Нарушение и опасность для других",
     ["Sólo importa si llega a caerse", "Sólo se sanciona a los camiones"],
     ["Важно, только если упадёт", "Наказывают только грузовики"]),
    ("llevar bultos sueltos en el habitáculo", "незакреплённые вещи в салоне",
     "Salen despedidos al frenar de golpe", "При резком торможении летят вперёд",
     ["No suponen ningún riesgo real alguno", "Sólo molestan a los pasajeros detrás"],
     ["Никакого риска не несут", "Только мешают пассажирам"]),
]


def preguntas_carga():
    salida = []
    for es, ru, bien_es, bien_ru, mal_es, mal_ru in CARGA:
        salida.append({
            "t": "seguridad",
            "q": "¿Qué hay que saber sobre %s?" % es,
            "q_ru": "Что нужно знать про «%s»?" % ru,
            "o": [bien_es] + mal_es,
            "o_ru": [bien_ru] + mal_ru,
            "e": "%s: %s." % (ru.capitalize(), bien_ru.lower()),
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
              ("знаки", preguntas_senales()),
              ("реакция", preguntas_reaccion()),
              ("алкоголь", preguntas_alcohol()),
              ("категории", preguntas_permisos()),
              ("сроки", preguntas_plazos()),
              ("огни", preguntas_luces()),
              ("суммы", preguntas_importes()),
              ("приоритет", preguntas_prioridad()),
              ("безопасность", preguntas_seguridad_tabla()),
              ("документы", preguntas_documentos_tabla()),
              ("стоянка", preguntas_estacionar()),
              ("обгон", preguntas_adelantar()),
              ("манёвры", preguntas_maniobras()),
              ("авария", preguntas_accidente()),
              ("водитель", preguntas_conductor()),
              ("груз", preguntas_carga())]
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
