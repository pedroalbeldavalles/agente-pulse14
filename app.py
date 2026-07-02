from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import List
import json, shutil, uuid, datetime
from PIL import Image
from cerebro.brain import Pulse14Brain

BASE = Path(__file__).resolve().parent
PROJECTS = BASE / "proyectos"
PROJECTS.mkdir(exist_ok=True)

app = FastAPI(title="Motor Pulse14 Núcleo v1")
app.mount("/interfaz", StaticFiles(directory=str(BASE / "interfaz")), name="interfaz")
app.mount("/proyectos", StaticFiles(directory=str(PROJECTS)), name="proyectos")

@app.get("/")
def home():
    return FileResponse(BASE / "interfaz" / "index.html")

@app.post("/api/proyecto/crear")
async def crear_proyecto(nombre: str = Form("Proyecto Pulse14")):
    pid = "P14-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    pdir = PROJECTS / pid
    (pdir / "imagenes").mkdir(parents=True)
    project = {
        "id": pid,
        "nombre": nombre,
        "fecha_creacion": datetime.datetime.now().isoformat(),
        "imagenes": [],
        "porcentajes": [],
        "cerebro": Pulse14Brain.estado_inicial(),
        "historial": [{"evento": "proyecto_creado", "fecha": datetime.datetime.now().isoformat()}],
        "paquete_ia": None
    }
    (pdir / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return project

@app.post("/api/proyecto/{pid}/imagenes")
async def subir_imagenes(pid: str, imagenes: List[UploadFile] = File(...)):
    pdir = PROJECTS / pid
    if not (pdir / "project.json").exists():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    project = json.loads((pdir / "project.json").read_text(encoding="utf-8"))
    for f in imagenes:
        ext = Path(f.filename).suffix.lower() or ".png"
        fname = uuid.uuid4().hex[:10] + ext
        dest = pdir / "imagenes" / fname
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        try:
            im = Image.open(dest)
            w, h = im.size
        except Exception:
            w, h = None, None
        project["imagenes"].append({
            "archivo_original": f.filename,
            "archivo_guardado": fname,
            "url": f"/proyectos/{pid}/imagenes/{fname}",
            "resolucion": {"ancho": w, "alto": h},
            "tipo": f.content_type
        })
    n = len(project["imagenes"])
    base = 100 // n if n else 0
    resto = 100 - base * n
    project["porcentajes"] = [base + (1 if i < resto else 0) for i in range(n)]
    project["historial"].append({"evento": "imagenes_subidas", "cantidad": len(imagenes), "fecha": datetime.datetime.now().isoformat()})
    project["cerebro"] = Pulse14Brain.actualizar_estado(project)
    (pdir / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return project

@app.post("/api/proyecto/{pid}/paquete-ia")
async def crear_paquete_ia(pid: str, instrucciones: str = Form(""), colores_max: int = Form(15)):
    pdir = PROJECTS / pid
    if not (pdir / "project.json").exists():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    project = json.loads((pdir / "project.json").read_text(encoding="utf-8"))
    paquete = Pulse14Brain.crear_paquete_ia(project, instrucciones, colores_max)
    project["paquete_ia"] = paquete
    project["historial"].append({"evento": "paquete_ia_creado", "fecha": datetime.datetime.now().isoformat()})
    (pdir / "project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return project

@app.get("/api/proyecto/{pid}")
def leer_proyecto(pid: str):
    p = PROJECTS / pid / "project.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return json.loads(p.read_text(encoding="utf-8"))
