from __future__ import annotations
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from modulos.motor_pulse14 import crear_paquete_ia

app = FastAPI(title='Agente Pulse 14', version='1.8.0')
app.mount('/interfaz', StaticFiles(directory='interfaz', html=False), name='interfaz')

@app.get('/')
def inicio():
    return FileResponse('interfaz/index.html', headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'})

@app.get('/api/salud')
def salud():
    return {'ok': True, 'version': 'v8'}

def parse_porcentajes(texto: str) -> list[float]:
    try:
        return [float(x.strip().replace(',', '.')) for x in texto.split(',') if x.strip()]
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Los porcentajes deben ser números separados por coma.') from exc

@app.post('/api/preparar-paquete-ia')
async def preparar_paquete_ia(imagenes: list[UploadFile] = File(...), porcentajes: str = Form(...), modelo: str = Form('motor_pulse14'), estilo: str = Form('ilustracion_tecnica_bordado'), detalle: str = Form('medio'), paleta_colores: int = Form(15), instrucciones: str = Form('')):
    vals = parse_porcentajes(porcentajes)
    if len(imagenes) != len(vals):
        raise HTTPException(status_code=400, detail='El número de imágenes y porcentajes no coincide.')
    if round(sum(vals), 2) != 100:
        raise HTTPException(status_code=400, detail='La suma de porcentajes debe ser exactamente 100%.')
    archivos=[]
    for im in imagenes:
        archivos.append((im.filename or 'imagen', im.content_type or '', await im.read()))
    try:
        return crear_paquete_ia(archivos, vals, modelo, estilo, detalle, max(2, min(64, int(paleta_colores))), instrucciones or '')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Error preparando paquete IA: {exc}') from exc
