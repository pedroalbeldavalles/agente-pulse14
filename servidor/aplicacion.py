from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
INTERFAZ_DIR = BASE_DIR / "interfaz"

app = FastAPI(title="Agente Pulse 14", version="0.1.0")
app.mount("/interfaz", StaticFiles(directory=str(INTERFAZ_DIR)), name="interfaz")


@app.get("/")
def inicio():
    return FileResponse(INTERFAZ_DIR / "index.html")


@app.get("/api/estado")
def estado():
    return {"ok": True, "modulo": "subida-porcentajes", "version": "v2"}


@app.post("/api/validar-imagenes")
async def validar_imagenes(
    imagenes: List[UploadFile] = File(...),
    porcentajes_json: str = Form(...),
):
    try:
        porcentajes = json.loads(porcentajes_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Los porcentajes no tienen formato JSON válido.") from exc

    if not isinstance(porcentajes, list):
        raise HTTPException(status_code=400, detail="Los porcentajes deben enviarse como una lista.")

    if len(imagenes) != len(porcentajes):
        raise HTTPException(status_code=400, detail="Debe existir un porcentaje por cada imagen.")

    total = 0
    for valor in porcentajes:
        if not isinstance(valor, int):
            raise HTTPException(status_code=400, detail="Cada porcentaje debe ser un número entero.")
        if valor < 0 or valor > 100:
            raise HTTPException(status_code=400, detail="Cada porcentaje debe estar entre 0 y 100.")
        total += valor

    if total != 100:
        raise HTTPException(status_code=400, detail="La suma de porcentajes debe ser exactamente 100%.")

    informe = []
    for imagen, porcentaje in zip(imagenes, porcentajes):
        if not imagen.content_type or not imagen.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"{imagen.filename} no es una imagen válida.")
        contenido = await imagen.read()
        if not contenido:
            raise HTTPException(status_code=400, detail=f"{imagen.filename} está vacía.")
        try:
            from io import BytesIO
            img = Image.open(BytesIO(contenido))
            ancho, alto = img.size
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"No se pudo leer {imagen.filename} como imagen.") from exc
        informe.append({
            "nombre": imagen.filename,
            "tipo": imagen.content_type,
            "tamano_bytes": len(contenido),
            "resolucion": {"ancho": ancho, "alto": alto},
            "porcentaje": porcentaje,
        })

    return {
        "ok": True,
        "mensaje": "Imágenes y porcentajes validados correctamente.",
        "total_porcentaje": total,
        "imagenes": informe,
    }
