from __future__ import annotations
import hashlib

def crear_paquete_ia(archivos, porcentajes, modelo, estilo, detalle, paleta_colores, instrucciones):
    if len(archivos) != len(porcentajes):
        raise ValueError('El número de imágenes y porcentajes no coincide.')
    if round(sum(float(p) for p in porcentajes), 2) != 100:
        raise ValueError('La suma de porcentajes debe ser exactamente 100%.')
    usados=[]
    for (nombre, tipo, data), pct in zip(archivos, porcentajes):
        if float(pct) <= 0:
            continue
        if not tipo.startswith('image/'):
            raise ValueError(f'{nombre} no es una imagen válida.')
        usados.append({'nombre': nombre, 'tipo': tipo, 'porcentaje': float(pct), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()[:16]})
    prompt = (
        'Crear una imagen técnica de alta calidad para bordado y posterior vectorización.\n'
        'Usar las imágenes aportadas como referencias ponderadas por porcentaje.\n'
        f'Estilo: {estilo}. Nivel de detalle: {detalle}. Paleta máxima: {paleta_colores} colores.\n'
        'Requisitos: contornos cerrados, línea negra fina uniforme, colores planos, sin sombras, sin degradados, objetos independientes, preparado para CorelDRAW X7 y Pulse 14.\n'
        f'Instrucciones adicionales: {instrucciones or "ninguna"}.\n'
        f'Referencias: {usados}'
    )
    return {'ok': True, 'mensaje': 'Paquete enviado/preparado para el Motor IA Pulse14.', 'resumen': {'modelo': modelo, 'estilo': estilo, 'detalle': detalle, 'paleta_colores': paleta_colores, 'imagenes_usadas': len(usados), 'porcentaje_total': round(sum(float(p) for p in porcentajes), 2)}, 'imagenes': usados, 'prompt': prompt}
