from __future__ import annotations

import base64
import io
from dataclasses import dataclass, asdict
from typing import Any

from PIL import Image, ImageOps


@dataclass
class ImagenPreparada:
    indice: int
    nombre: str
    porcentaje: int
    content_type_original: str
    ancho_original: int
    alto_original: int
    ancho_preparado: int
    alto_preparado: int
    formato: str
    bytes_preparados: int
    data_url: str

    def resumen(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("data_url", None)
        return data


def preparar_imagen_referencia(
    indice: int,
    nombre: str,
    content_type: str,
    contenido: bytes,
    porcentaje: int,
    max_side: int = 1400,
) -> ImagenPreparada:
    if not contenido:
        raise ValueError(f"La imagen {nombre} está vacía.")

    try:
        img = Image.open(io.BytesIO(contenido))
        img = ImageOps.exif_transpose(img)
    except Exception as exc:
        raise ValueError(f"No se pudo leer la imagen {nombre}: {exc}") from exc

    ancho_original, alto_original = img.size

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    scale = min(1.0, max_side / max(img.size))
    if scale < 1.0:
        nuevo_ancho = max(1, int(img.size[0] * scale))
        nuevo_alto = max(1, int(img.size[1] * scale))
        img = img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)

    salida = io.BytesIO()
    img.save(salida, format="PNG", optimize=True)
    png = salida.getvalue()
    b64 = base64.b64encode(png).decode("ascii")

    return ImagenPreparada(
        indice=indice,
        nombre=nombre,
        porcentaje=int(porcentaje),
        content_type_original=content_type or "application/octet-stream",
        ancho_original=ancho_original,
        alto_original=alto_original,
        ancho_preparado=img.size[0],
        alto_preparado=img.size[1],
        formato="PNG",
        bytes_preparados=len(png),
        data_url=f"data:image/png;base64,{b64}",
    )
