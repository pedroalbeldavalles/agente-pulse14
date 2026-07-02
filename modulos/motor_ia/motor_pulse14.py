from __future__ import annotations

from typing import Any

from .crear_prompt import crear_prompt_pulse14
from .preparar_imagenes import ImagenPreparada


class ProveedorIANoConfigurado(RuntimeError):
    pass


def preparar_paquete_ia(
    imagenes: list[ImagenPreparada],
    modelo: str,
    estilo: str,
    detalle: str,
    paleta_colores: int,
    instrucciones: str | None,
) -> dict[str, Any]:
    prompt = crear_prompt_pulse14(
        imagenes=imagenes,
        estilo=estilo,
        detalle=detalle,
        paleta_colores=paleta_colores,
        instrucciones=instrucciones,
    )

    return {
        "modelo": modelo,
        "estilo": estilo,
        "detalle": detalle,
        "paleta_colores": paleta_colores,
        "prompt": prompt,
        "imagenes": [img.resumen() for img in imagenes],
    }


def generar_dibujo_con_motor_ia(paquete: dict[str, Any]) -> dict[str, Any]:
    """Aquí se conectará el proveedor IA real en el módulo 2.

    En este módulo 1 no generamos dibujo todavía. Solo comprobamos que el paquete
    técnico que se enviará al proveedor IA está correcto.
    """
    raise ProveedorIANoConfigurado(
        "Módulo 1 correcto: imágenes, porcentajes y prompt preparados. "
        "Falta conectar el proveedor IA real en el Módulo 2."
    )
