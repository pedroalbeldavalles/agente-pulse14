from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from modulos.motor_pulse14 import crear_paquete_ia

aplicacion = FastAPI(title="Agente Pulse 14", version="1.2.0")

# Alias necesario para Hugging Face / Uvicorn cuando arranca con servidor.aplicacion:app
app = aplicacion

aplicacion.mount("/interfaz", StaticFiles(directory="interfaz"), name="interfaz")


@aplicacion.get("/")
def inicio():
    return FileResponse("interfaz/index.html")


@aplicacion.get("/api/salud")
def salud():
    return {"ok": True, "modulo": "agente-pulse14-modulo-1-preparacion-ia"}


def _parse_porcentajes(texto: str) -> list[int]:
    try:
        valores = [int(x.strip()) for x in texto.split(",") if x.strip() != ""]
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Los porcentajes deben ser números enteros separados por coma.") from exc
    return valores


@aplicacion.post("/api/validar-imagenes")
async def validar_imagenes(
    imagenes: list[UploadFile] = File(...),
    porcentajes: str = Form(...),
):
    valores = _parse_porcentajes(porcentajes)
    if len(imagenes) != len(valores):
        raise HTTPException(status_code=400, detail="El número de imágenes y porcentajes no coincide.")
    if sum(valores) != 100:
        raise HTTPException(status_code=400, detail="La suma de porcentajes debe ser exactamente 100%.")
    if any(v < 0 or v > 100 for v in valores):
        raise HTTPException(status_code=400, detail="Cada porcentaje debe estar entre 0 y 100%.")

    usadas = []
    for imagen, porcentaje in zip(imagenes, valores):
        if porcentaje <= 0:
            continue
        if not imagen.content_type or not imagen.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"{imagen.filename} no es una imagen válida.")
        usadas.append({"nombre": imagen.filename, "porcentaje": porcentaje, "tipo": imagen.content_type})

    return {"ok": True, "imagenes_usadas": usadas, "porcentaje_total": sum(valores)}


@aplicacion.post("/api/preparar-paquete-ia")
async def preparar_paquete_ia(
    imagenes: list[UploadFile] = File(...),
    porcentajes: str = Form(...),
    modelo: str = Form("pendiente"),
    estilo: str = Form("ilustracion_tecnica_bordado"),
    detalle: str = Form("medio"),
    paleta_colores: int = Form(15),
    instrucciones: str = Form(""),
):
    valores = _parse_porcentajes(porcentajes)
    if len(imagenes) != len(valores):
        raise HTTPException(status_code=400, detail="El número de imágenes y porcentajes no coincide.")
    if sum(valores) != 100:
        raise HTTPException(status_code=400, detail="La suma de porcentajes debe ser exactamente 100%.")

    archivos = []
    for imagen in imagenes:
        data = await imagen.read()
        archivos.append((imagen.filename or "imagen", imagen.content_type or "", data))

    try:
        paquete = crear_paquete_ia(
            archivos=archivos,
            porcentajes=valores,
            modelo=modelo,
            estilo=estilo,
            detalle=detalle,
            paleta_colores=max(2, min(64, int(paleta_colores))),
            instrucciones=instrucciones or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error preparando paquete IA: {exc}") from exc

    return paquete
