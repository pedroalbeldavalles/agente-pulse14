# Módulo 1 - Preparación IA v2

Objetivo: preparar correctamente las imágenes y porcentajes antes de conectar el motor IA real.

Incluye:

- Reparto automático por defecto a partes iguales al subir imágenes.
- Control numérico de porcentaje por imagen.
- Impide superar el 100%.
- Botón activo solo cuando la suma es exactamente 100%.
- Envío real al servidor de imágenes + porcentajes + parámetros.
- Endpoint `/api/preparar-paquete-ia`.
- Creación de prompt técnico Pulse 14.
- Respuesta JSON con resumen, prompt y metadatos.

Este módulo NO genera todavía una imagen IA. El siguiente módulo conectará el proveedor IA real.

Archivos que sustituye o añade:

- interfaz/index.html
- interfaz/estilos.css
- interfaz/app.js
- servidor/aplicacion.py
- modulos/motor_pulse14.py
- modulos/__init__.py
- requirements.txt


## Corrección v3

- Al subir imágenes, el porcentaje se reparte automáticamente a partes iguales entre todas.
- Ejemplo: 2 imágenes = 50/50; 3 imágenes = 34/33/33; 4 imágenes = 25/25/25/25.
- Al eliminar una imagen, se vuelve a repartir automáticamente entre las restantes.


## Corrección v4

- Se cambia el botón principal a **Crear imagen con IA**.
- El botón llama a `/api/preparar-paquete-ia`.
- Se añade `app.py` en la raíz para facilitar el arranque en Hugging Face Spaces con Uvicorn.
- Esta versión es la que debe sustituir a la publicada si el Space muestra la interfaz antigua.
