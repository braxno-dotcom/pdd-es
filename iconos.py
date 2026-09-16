# -*- coding: utf-8 -*-
"""Рисует значки сайта для телефона:  python iconos.py

⚠️ Зачем PNG, если в странице уже есть SVG-значок: iOS для ярлыка на домашнем экране
SVG не берёт вовсе, а Android берёт только то, что перечислено в manifest.json.
Без этих файлов ярлык на телефоне выходит серым квадратом с буквой браузера.

Рисуем испанский флаг (красный — жёлтый — красный, цвета государственные) и поверх
крупно «ПДД»: на экране телефона значок читается размером с ноготь, поэтому ни имени
сайта, ни мелких деталей туда не влезет — только флаг и три буквы.
"""
from PIL import Image, ImageDraw, ImageFont

ROJO = (170, 21, 27)        # AA151B — красный флага Испании
AMARILLO = (241, 191, 0)    # F1BF00 — жёлтый флага Испании
OSCURO = (15, 23, 42)       # цвет сайта, для текста на жёлтом

TAMANOS = [(180, "icono-180.png"),   # apple-touch-icon: ярлык на айфоне
           (192, "icono-192.png"),   # manifest: ярлык на андроиде
           (512, "icono-512.png")]   # manifest: витрина установки и сплэш


def fuente(px):
    for camino in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf"):
        try:
            return ImageFont.truetype(camino, px)
        except OSError:
            continue
    return ImageFont.load_default()


def dibujar(lado):
    img = Image.new("RGB", (lado, lado), ROJO)
    d = ImageDraw.Draw(img)
    # Полосы флага: у испанского средняя вдвое шире крайних.
    d.rectangle([0, lado // 4, lado, lado * 3 // 4], fill=AMARILLO)

    texto = "ПДД"
    px = int(lado * 0.34)
    f = fuente(px)
    # Подгоняем, чтобы три буквы влезли с полями по краям.
    while d.textlength(texto, font=f) > lado * 0.78 and px > 8:
        px -= 2
        f = fuente(px)
    ancho = d.textlength(texto, font=f)
    caja = d.textbbox((0, 0), texto, font=f)
    alto = caja[3] - caja[1]
    d.text(((lado - ancho) / 2, (lado - alto) / 2 - caja[1]), texto, font=f, fill=OSCURO)
    return img


if __name__ == "__main__":
    for lado, nombre in TAMANOS:
        dibujar(lado).save(nombre, "PNG", optimize=True)
        print("нарисован", nombre)
