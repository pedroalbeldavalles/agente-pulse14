---
title: Agente Pulse 14 V7
emoji: 🧵
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Agente Pulse 14

Sistema para la transformación inteligente de imágenes orientadas a bordado profesional mediante Inteligencia Artificial.

## Estado del proyecto

Actualmente este repositorio contiene el **Módulo 1: Preparación IA**.

Este módulo permite:

- Subir varias imágenes.
- Repartir automáticamente el 100% entre las imágenes cargadas.
- Modificar porcentajes de forma numérica.
- Controlar que la suma total sea exactamente 100%.
- Preparar un paquete técnico para un futuro motor IA.
- Generar un prompt técnico orientado a CorelDRAW X7, Pulse 14 y bordado.

## Estructura del proyecto

```text
interfaz/
modulos/
servidor/
app.py
requirements.txt
Dockerfile
README.md
README_MODULO_1.md
```

## Funcionamiento actual

El botón **Crear imagen con IA** todavía no genera la imagen final.

En esta fase prepara y devuelve el paquete que después usará el motor IA real.

## Próximas fases

1. Conexión con motor IA real.
2. Generación de imagen de alta calidad.
3. Control de calidad.
4. Corrección automática.
5. Exportación SVG.
6. Exportación EPS.
7. Exportación AI.
8. Exportación EMF.
9. Preparación final para Pulse 14.
