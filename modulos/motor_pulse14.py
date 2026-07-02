from __future__ import annotations
from datetime import datetime
import hashlib


def crear_paquete_ia(archivos, porcentajes, modelo, estilo, detalle, paleta_colores, instrucciones):
    if not archivos:
        raise ValueError("Debe haber al menos una imagen.")
    total = round(sum(float(p) for p in porcentajes), 2)
    if total != 100:
        raise ValueError("La suma de porcentajes debe ser exactamente 100%.")

    imagenes = []
    for idx, ((nombre, content_type, contenido), porcentaje) in enumerate(zip(archivos, porcentajes), start=1):
        digest = hashlib.sha256(contenido).hexdigest()[:16]
        imagenes.append({
            "orden": idx,
            "nombre": nombre,
            "tipo": content_type,
            "bytes": len(contenido),
            "porcentaje": float(porcentaje),
            "hash": digest,
        })

    prompt = construir_prompt(imagenes, estilo, detalle, paleta_colores, instrucciones)
    return {
        "ok": True,
        "mensaje": "Paquete preparado para el Motor IA Pulse14.",
        "version": "V11",
        "fecha": datetime.utcnow().isoformat() + "Z",
        "resumen": {
            "imagenes_recibidas": len(imagenes),
            "porcentaje_total": total,
            "modelo": modelo,
            "estilo": estilo,
            "detalle": detalle,
            "paleta_colores": paleta_colores,
        },
        "imagenes": imagenes,
        "prompt": prompt,
    }


def construir_prompt(imagenes, estilo, detalle, paleta_colores, instrucciones):
    refs = "\n".join(
        f"- Imagen {i['orden']}: {i['nombre']} aporta {i['porcentaje']}% al resultado."
        for i in imagenes
    )
    extra = instrucciones.strip() or "Sin instrucciones adicionales."
    return f"""Crear un dibujo de alta calidad para bordado y vectorización Pulse14.

REFERENCIAS:
{refs}

OBJETIVO:
- Interpretar las imágenes como referencias visuales, respetando sus porcentajes.
- Crear un dibujo ornamental limpio, no una copia pixelada.
- Primero construir todos los contornos cerrados.
- Después rellenar cada zona con un único color plano.
- Cada pétalo, hoja, cinta, tallo y detalle debe ser un objeto independiente.
- Sin sombras.
- Sin degradados.
- Sin texturas.
- Sin transparencias.
- Línea negra fina y uniforme.
- Máximo {paleta_colores} colores reales.
- Preparado para futura vectorización SVG, EMF, EPS, AI y Pulse14.

PARÁMETROS:
- Estilo: {estilo}
- Nivel de detalle: {detalle}

INSTRUCCIONES DEL USUARIO:
{extra}
"""
