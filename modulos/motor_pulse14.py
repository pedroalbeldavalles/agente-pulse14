from __future__ import annotations

import base64
import io
import json
from dataclasses import asdict, dataclass
from typing import Any

from PIL import Image, ImageOps


@dataclass
class ImagenPreparada:
    indice: int
    nombre: str
    porcentaje: int
    tipo_original: str
    ancho_original: int
    alto_original: int
    ancho_preparado: int
    alto_preparado: int
    formato_preparado: str
    bytes_preparados: int
    data_url: str


@dataclass
class PaqueteIA:
    imagenes: list[ImagenPreparada]
    modelo: str
    estilo: str
    detalle: str
    paleta_colores: int
    instrucciones: str
    prompt: str


def _normalizar_imagen(data: bytes, max_side: int = 1400) -> tuple[bytes, int, int, int, int]:
    """Corrige orientación, elimina metadatos y convierte a PNG."""
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    ancho_original, alto_original = img.size

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    scale = min(1.0, max_side / max(img.size))
    if scale < 1.0:
        nuevo = (max(1, int(img.size[0] * scale)), max(1, int(img.size[1] * scale)))
        img = img.resize(nuevo, Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue(), ancho_original, alto_original, img.size[0], img.size[1]


def preparar_imagenes_para_ia(
    archivos: list[tuple[str, str, bytes]],
    porcentajes: list[int],
) -> list[ImagenPreparada]:
    if len(archivos) != len(porcentajes):
        raise ValueError("El número de imágenes y porcentajes no coincide.")
    if sum(porcentajes) != 100:
        raise ValueError("La suma de porcentajes debe ser exactamente 100%.")
    if any(p < 0 or p > 100 for p in porcentajes):
        raise ValueError("Cada porcentaje debe estar entre 0 y 100%.")

    preparadas: list[ImagenPreparada] = []
    for idx, ((nombre, content_type, data), porcentaje) in enumerate(zip(archivos, porcentajes), start=1):
        if porcentaje <= 0:
            continue
        if not content_type.startswith("image/"):
            raise ValueError(f"{nombre} no es una imagen válida.")
        png, w0, h0, w1, h1 = _normalizar_imagen(data)
        b64 = base64.b64encode(png).decode("ascii")
        preparadas.append(
            ImagenPreparada(
                indice=idx,
                nombre=nombre,
                porcentaje=porcentaje,
                tipo_original=content_type,
                ancho_original=w0,
                alto_original=h0,
                ancho_preparado=w1,
                alto_preparado=h1,
                formato_preparado="PNG",
                bytes_preparados=len(png),
                data_url=f"data:image/png;base64,{b64}",
            )
        )

    if not preparadas:
        raise ValueError("Debe haber al menos una imagen con porcentaje mayor que 0%.")

    return preparadas


def construir_prompt_pulse14(
    imagenes: list[ImagenPreparada],
    estilo: str,
    detalle: str,
    paleta_colores: int,
    instrucciones: str = "",
) -> str:
    detalle_txt = {
        "bajo": "simplificar bastante, conservar solo formas principales y eliminar detalles pequeños",
        "medio": "equilibrar fidelidad y limpieza, conservar los elementos importantes",
        "alto": "conservar muchos detalles, siempre como formas cerradas, limpias y separadas",
    }.get(detalle, detalle)

    estilo_txt = {
        "ilustracion_tecnica_bordado": "ilustración técnica para bordado",
        "ornamental_vectorial": "dibujo ornamental vectorial limpio",
        "linea_y_color_plano": "línea limpia con colores planos",
    }.get(estilo, estilo)

    lineas = [
        "Crear un dibujo técnico nuevo para bordado y vectorización a partir de varias imágenes de referencia.",
        "",
        "Peso de las imágenes de referencia:",
    ]
    for img in imagenes:
        lineas.append(f"- Imagen {img.indice}: {img.nombre} -> {img.porcentaje}% de influencia")

    lineas += [
        "",
        "Interpretación de los porcentajes:",
        "- Las imágenes con mayor porcentaje dominan composición, proporción y motivos principales.",
        "- Las imágenes con menor porcentaje aportan detalles, formas secundarias, colores o adornos.",
        "- No copiar como fotografía: reinterpretar como dibujo técnico limpio.",
        "",
        "Requisitos obligatorios del resultado:",
        "- Formas cerradas.",
        "- Colores sólidos y planos.",
        "- Sin textura fotográfica.",
        "- Sin degradados.",
        "- Sin sombras realistas.",
        "- Bordes claros.",
        "- Elementos separados: pétalos, hojas, tallos, cintas y adornos.",
        "- Preparado para reducción de colores y vectorización posterior.",
        "- Preparado para generar SVG limpio, EMF, EPS y AI compatible.",
        f"- Estilo: {estilo_txt}.",
        f"- Nivel de detalle: {detalle_txt}.",
        f"- Paleta máxima objetivo: {paleta_colores} colores.",
    ]
    if instrucciones.strip():
        lineas += ["", "Instrucciones adicionales del usuario:", instrucciones.strip()]
    return "\n".join(lineas)


def crear_paquete_ia(
    archivos: list[tuple[str, str, bytes]],
    porcentajes: list[int],
    modelo: str,
    estilo: str,
    detalle: str,
    paleta_colores: int,
    instrucciones: str,
) -> dict[str, Any]:
    imagenes = preparar_imagenes_para_ia(archivos, porcentajes)
    prompt = construir_prompt_pulse14(imagenes, estilo, detalle, paleta_colores, instrucciones)
    paquete = PaqueteIA(
        imagenes=imagenes,
        modelo=modelo,
        estilo=estilo,
        detalle=detalle,
        paleta_colores=paleta_colores,
        instrucciones=instrucciones,
        prompt=prompt,
    )
    return {
        "ok": True,
        "modulo": "preparacion_ia_v1",
        "mensaje": "Paquete IA preparado correctamente. El siguiente módulo conectará el motor IA real.",
        "resumen": {
            "imagenes_recibidas": len(archivos),
            "imagenes_usadas": len(imagenes),
            "porcentaje_total": sum(porcentajes),
            "modelo": modelo,
            "estilo": estilo,
            "detalle": detalle,
            "paleta_colores": paleta_colores,
        },
        "prompt": prompt,
        "imagenes": [asdict(img) for img in imagenes],
    }
