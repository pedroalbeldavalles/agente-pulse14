from datetime import datetime

class Pulse14Brain:
    @staticmethod
    def estado_inicial():
        return {
            "version": "nucleo_v1",
            "objetivo": "crear dibujo de alta resolucion para bordado y vectorizacion",
            "reglas_obligatorias": [
                "contornos completamente cerrados",
                "cada objeto independiente",
                "relleno con un unico color plano por zona",
                "sin sombras",
                "sin degradados",
                "sin texturas",
                "linea negra fina y uniforme",
                "preparado para SVG, EMF, EPS, AI, CorelDRAW y Pulse14"
            ],
            "estado": "inicializado"
        }

    @staticmethod
    def actualizar_estado(project):
        estado = Pulse14Brain.estado_inicial()
        estado["imagenes_cargadas"] = len(project.get("imagenes", []))
        estado["porcentajes"] = project.get("porcentajes", [])
        estado["estado"] = "imagenes_preparadas" if project.get("imagenes") else "sin_imagenes"
        return estado

    @staticmethod
    def crear_paquete_ia(project, instrucciones, colores_max):
        refs = []
        for img, pct in zip(project.get("imagenes", []), project.get("porcentajes", [])):
            refs.append({
                "archivo": img["archivo_original"],
                "url": img["url"],
                "peso": pct
            })
        prompt = f"""
Crear un dibujo técnico ornamental de alta resolución a partir de las imágenes de referencia.

REGLAS OBLIGATORIAS:
- Primero interpretar la imagen como objetos: flores, pétalos, hojas, cintas, tallos, adornos y detalles.
- Crear todos los contornos completamente cerrados.
- Cada pétalo, hoja, cinta, tallo y detalle debe ser un objeto independiente.
- Después rellenar cada contorno con un único color plano.
- No usar sombras.
- No usar degradados.
- No usar texturas.
- No usar transparencias.
- Usar máximo {colores_max} colores reales.
- Usar línea negra fina, limpia y uniforme.
- Fondo eliminado o transparente.
- Resultado preparado para bordado industrial, CorelDRAW, Pulse14 y vectorización posterior.

INSTRUCCIONES DEL USUARIO:
{instrucciones or 'Sin instrucciones adicionales.'}

IMÁGENES DE REFERENCIA Y PESOS:
""".strip()
        for r in refs:
            prompt += f"\n- {r['archivo']}: {r['peso']}%"
        return {
            "fecha": datetime.now().isoformat(),
            "tipo": "paquete_ia_pulse14",
            "imagenes_referencia": refs,
            "colores_maximos": colores_max,
            "instrucciones": instrucciones,
            "prompt": prompt,
            "estado": "preparado_para_conector_ia"
        }
