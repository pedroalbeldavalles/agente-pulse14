from __future__ import annotations

from .preparar_imagenes import ImagenPreparada


def crear_prompt_pulse14(
    imagenes: list[ImagenPreparada],
    estilo: str,
    detalle: str,
    paleta_colores: int,
    instrucciones: str | None = None,
) -> str:
    lineas: list[str] = []

    lineas.append("Crea un dibujo técnico para bordado y vectorización a partir de varias imágenes de referencia.")
    lineas.append("")
    lineas.append("Interpretación de porcentajes:")
    lineas.append("- El porcentaje indica cuánto debe influir cada imagen en el dibujo final.")
    lineas.append("- La imagen con mayor porcentaje debe tener más peso en composición, estructura y motivo principal.")
    lineas.append("- Las imágenes con menor porcentaje deben aportar detalles, formas secundarias, color o estilo visual.")
    lineas.append("")
    lineas.append("Imágenes de referencia:")
    for img in imagenes:
        lineas.append(f"- Imagen {img.indice}: {img.nombre} -> {img.porcentaje}% de influencia.")

    lineas.append("")
    lineas.append("Objetivo visual obligatorio:")
    lineas.append("- No crear una fotografía.")
    lineas.append("- Crear una ilustración técnica limpia para bordado.")
    lineas.append("- Mantener el motivo y composición general de las referencias según sus porcentajes.")
    lineas.append("- Formas cerradas y bien separadas.")
    lineas.append("- Pétalos, hojas, tallos, cintas y adornos como zonas independientes.")
    lineas.append("- Colores planos y sólidos.")
    lineas.append("- Sin textura fotográfica, ruido, grano, brillos ni sombras realistas.")
    lineas.append("- Sin degradados.")
    lineas.append("- Bordes claros preparados para contorno negro posterior.")
    lineas.append("- Preparado para reducción posterior de paleta y vectorización SVG.")
    lineas.append("")
    lineas.append(f"Estilo: {estilo}.")
    lineas.append(f"Nivel de detalle: {detalle}.")
    lineas.append(f"Paleta objetivo máxima posterior: {paleta_colores} colores.")

    if instrucciones and instrucciones.strip():
        lineas.append("")
        lineas.append("Instrucciones adicionales del usuario:")
        lineas.append(instrucciones.strip())

    return "\n".join(lineas)
