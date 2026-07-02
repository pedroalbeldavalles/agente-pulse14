---
title: Agente Pulse 14
emoji: 🧵
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app.py
pinned: false

# \---Agente Pulse 14 - Módulo 1 Preparación IA v4

Esta versión sustituye la publicada si en Hugging Face no aparece el reparto automático ni el botón para IA.

Incluye:

* Subida de varias imágenes.
* Reparto automático del 100% entre todas las imágenes subidas.
* Reparto automático al eliminar imágenes.
* Porcentajes numéricos editables.
* Bloqueo para que la suma no supere el 100%.
* Botón **Crear imagen con IA**.
* Envío real al endpoint `/api/preparar-paquete-ia`.
* Generación de prompt técnico Pulse 14 y paquete JSON para el futuro motor IA real.

## Ejecutar en local

```bash
pip install -r requirements.txt
uvicorn app:aplicacion --host 0.0.0.0 --port 7860
```

Después abrir:

```text
http://localhost:7860
```

## En Hugging Face Spaces

Sube todos estos archivos respetando la estructura de carpetas. El Space debe arrancar con:

```bash
uvicorn app:aplicacion --host 0.0.0.0 --port 7860
```

Si el Space sigue mostrando el interfaz antiguo, revisa que hayas reemplazado `interfaz/index.html`, `interfaz/app.js`, `servidor/aplicacion.py`, `modulos/motor\\\_pulse14.py` y que exista `app.py` en la raíz.


