from __future__ import annotations

import base64
import io
import math
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps

ANALISIS_CACHE: dict[str, dict[str, Any]] = {}


def _decode_image(data: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img = ImageOps.exif_transpose(img)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def _resize_max(img: np.ndarray, max_side: int = 1200) -> tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    s = min(1.0, max_side / max(h, w))
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img, s


def _svg_path_from_contour(cnt: np.ndarray, ox: int = 0, oy: int = 0) -> str:
    pts = cnt.reshape(-1, 2)
    if len(pts) < 3:
        return ""
    # Simplificación suave, suficiente para visor y posterior vectorización inicial.
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, max(0.8, peri * 0.004), True).reshape(-1, 2)
    d = [f"M {approx[0][0]-ox:.1f} {approx[0][1]-oy:.1f}"]
    for x, y in approx[1:]:
        d.append(f"L {x-ox:.1f} {y-oy:.1f}")
    d.append("Z")
    return " ".join(d)


def _mask_foreground(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    # Color probable de fondo: mediana de esquinas.
    m = max(10, int(min(h, w) * 0.08))
    corners = np.vstack([
        img[:m, :m].reshape(-1, 3), img[:m, -m:].reshape(-1, 3),
        img[-m:, :m].reshape(-1, 3), img[-m:, -m:].reshape(-1, 3)
    ])
    bg = np.median(corners, axis=0).astype(np.uint8).reshape(1, 1, 3)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.int32)
    bglab = cv2.cvtColor(bg, cv2.COLOR_BGR2LAB).astype(np.int32)[0, 0]
    dist = np.sqrt(np.sum((lab - bglab) ** 2, axis=2))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    # Mantiene bordados coloreados aunque el fondo sea oscuro o claro.
    mask = ((dist > 24) & ((sat > 35) | (val > 170) | (val < 70))).astype(np.uint8) * 255
    mask = cv2.medianBlur(mask, 5)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def _quantize(img: np.ndarray, fg_mask: np.ndarray, k: int = 12) -> np.ndarray:
    pixels = img[fg_mask > 0].reshape(-1, 3).astype(np.float32)
    if len(pixels) < 100:
        return np.zeros(img.shape[:2], dtype=np.int32)
    if len(pixels) > 50000:
        idx = np.random.default_rng(123).choice(len(pixels), 50000, replace=False)
        sample = pixels[idx]
    else:
        sample = pixels
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
    _, _, centers = cv2.kmeans(sample, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    lab_centers = cv2.cvtColor(centers.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.int16)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.int16)
    flat = lab.reshape(-1, 3)
    # Distancia al centro más cercano.
    dists = np.sum((flat[:, None, :] - lab_centers[None, :, :]) ** 2, axis=2)
    labels = np.argmin(dists, axis=1).reshape(img.shape[:2]).astype(np.int32)
    labels[fg_mask == 0] = -1
    return labels


def _color_family(crop: np.ndarray, mask: np.ndarray) -> str:
    if np.count_nonzero(mask) == 0:
        return "motivo"
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    pix = hsv[mask > 0]
    h = float(np.median(pix[:, 0])); s = float(np.median(pix[:, 1])); v = float(np.median(pix[:, 2]))
    if s < 45 and v > 160: return "ornamento claro"
    if 35 <= h <= 90 and s > 35: return "hoja"
    if h < 10 or h > 165: return "flor roja/rosa"
    if 95 <= h <= 135: return "flor azul"
    if 15 <= h <= 35: return "flor amarilla/dorada"
    if 130 <= h <= 165: return "flor morada"
    return "motivo"


def _classify(crop: np.ndarray, mask: np.ndarray, w: int, h: int) -> tuple[str, str]:
    fam = _color_family(crop, mask)
    ratio = w / max(1, h)
    area_ratio = np.count_nonzero(mask) / max(1, w*h)
    if "hoja" in fam:
        return "hoja", "Hoja detectada"
    if ratio > 2.4 or ratio < 0.35:
        return "tallo", "Tallo / rama"
    if area_ratio < 0.28 and (ratio > 1.7 or ratio < 0.6):
        return "voluta", "Voluta / adorno curvo"
    if "flor" in fam:
        return "flor", fam.capitalize()
    return "ornamento", fam.capitalize()


def _make_svg_for_crop(labels: np.ndarray, x: int, y: int, w: int, h: int, component_mask: np.ndarray) -> tuple[str, int]:
    paths: list[str] = []
    # Contorno exterior del componente.
    comp_crop = component_mask[y:y+h, x:x+w]
    contours, _ = cv2.findContours(comp_crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 20:
            p = _svg_path_from_contour(cnt, 0, 0)
            if p: paths.append(p)
    # Regiones internas por grupos de color. Cada región se cierra y será 1 color.
    lab_crop = labels[y:y+h, x:x+w]
    for lab_id in sorted([int(v) for v in np.unique(lab_crop) if v >= 0]):
        m = ((lab_crop == lab_id).astype(np.uint8) * 255)
        m = cv2.bitwise_and(m, comp_crop)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3), np.uint8), iterations=1)
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            if cv2.contourArea(cnt) > 18:
                p = _svg_path_from_contour(cnt, 0, 0)
                if p: paths.append(p)
    # El SVG muestra contornos reales del motivo, no iconos de prueba.
    body = "\n".join(f'<path d="{p}" />' for p in paths[:80])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="white"/>
  <g fill="none" stroke="#111" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">
  {body}
  </g>
</svg>'''
    return svg, len(paths)


def _svg_data_url(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def analizar_imagenes_reales(archivos: list[tuple[str, str, bytes]], porcentajes: list[float], complejidad: str = "media") -> dict[str, Any]:
    motivos: list[dict[str, Any]] = []
    resumen_imgs: list[dict[str, Any]] = []
    max_motivos_por_imagen = {"simple": 18, "media": 32, "alta": 48, "muy_alta": 70}.get(complejidad, 32)

    for img_idx, ((nombre, content_type, data), pct) in enumerate(zip(archivos, porcentajes), start=1):
        img0 = _decode_image(data)
        img, scale = _resize_max(img0, 1200)
        h_img, w_img = img.shape[:2]
        fg = _mask_foreground(img)
        labels = _quantize(img, fg, k=14 if complejidad in {"alta", "muy_alta"} else 10)
        img_area = w_img * h_img
        raw_candidates = []

        def add_components(source_mask: np.ndarray, source_name: str):
            n, comp_local, stats_local, _ = cv2.connectedComponentsWithStats(source_mask, 8)
            for cid in range(1, n):
                x, y, w, h, area = stats_local[cid]
                if area < img_area * 0.00045 or w < 18 or h < 18:
                    continue
                if area > img_area * 0.22:
                    continue
                raw_candidates.append((int(area), int(x), int(y), int(w), int(h), (comp_local == cid).astype(np.uint8) * 255, source_name))

        # Componentes generales.
        add_components(fg, "foreground")
        # Componentes por región de color: esto separa pétalos, hojas y zonas internas,
        # evitando que un ramillete entero se convierta en un único bloque.
        for lab_id in [int(v) for v in np.unique(labels) if v >= 0]:
            cm = ((labels == lab_id).astype(np.uint8) * 255)
            cm = cv2.morphologyEx(cm, cv2.MORPH_OPEN, np.ones((3,3),np.uint8), iterations=1)
            add_components(cm, f"color_{lab_id}")

        # Elimina duplicados por cajas casi iguales.
        raw_candidates = sorted(raw_candidates, reverse=True, key=lambda t: t[0])
        candidates = []
        def iou(a,b):
            ax,ay,aw,ah=a; bx,by,bw,bh=b
            ix=max(0,min(ax+aw,bx+bw)-max(ax,bx)); iy=max(0,min(ay+ah,by+bh)-max(ay,by))
            inter=ix*iy; union=aw*ah+bw*bh-inter
            return inter/max(1,union)
        for cand in raw_candidates:
            _, x,y,w,h, cmask, src = cand
            if any(iou((x,y,w,h),(c[1],c[2],c[3],c[4]))>0.72 for c in candidates):
                continue
            candidates.append(cand)
            if len(candidates) >= max_motivos_por_imagen:
                break

        counts = {"flor": 0, "hoja": 0, "tallo": 0, "voluta": 0, "ornamento": 0}
        for area, x, y, w, h, cc_mask, src in candidates:
            pad = max(6, int(max(w, h) * 0.08))
            x0, y0 = max(0, x-pad), max(0, y-pad)
            x1, y1 = min(w_img, x+w+pad), min(h_img, y+h+pad)
            crop = img[y0:y1, x0:x1]
            crop_mask = cc_mask[y0:y1, x0:x1]
            tipo, desc = _classify(crop, crop_mask, x1-x0, y1-y0)
            counts[tipo] = counts.get(tipo, 0) + 1
            svg, regiones = _make_svg_for_crop(labels, x0, y0, x1-x0, y1-y0, cc_mask)
            mid = f"I{img_idx}_{tipo.upper()}_{counts[tipo]:02d}"
            motivos.append({
                "id": mid,
                "imagen": img_idx,
                "nombre_imagen": nombre,
                "aportacion": pct,
                "tipo": tipo,
                "titulo": f"{mid} · {desc}",
                "descripcion": f"Extraído realmente de la imagen {img_idx}. Regiones cerradas detectadas: {regiones}.",
                "complejidad": "alta" if regiones >= 18 else "media" if regiones >= 8 else "simple",
                "regiones": regiones,
                "bbox": [int(x0/scale), int(y0/scale), int((x1-x0)/scale), int((y1-y0)/scale)],
                "svg": svg,
                "svg_data": _svg_data_url(svg),
                "seleccionado": True,
            })
        resumen_imgs.append({
            "imagen": img_idx,
            "nombre": nombre,
            "aportacion": pct,
            "motivos_detectados": len(candidates),
            "flores": counts.get("flor",0),
            "hojas": counts.get("hoja",0),
            "tallos": counts.get("tallo",0),
            "volutas": counts.get("voluta",0),
            "ornamentos": counts.get("ornamento",0),
            "resolucion": f"{img0.shape[1]} × {img0.shape[0]}",
        })

    analisis_id = str(uuid.uuid4())
    ANALISIS_CACHE[analisis_id] = {"motivos": motivos, "resumen": resumen_imgs, "created": time.time()}
    return {
        "ok": True,
        "analisis_id": analisis_id,
        "resumen": resumen_imgs,
        "motivos": motivos,
        "total_motivos": len(motivos),
        "nota": "Biblioteca visual creada a partir de contornos reales detectados en las imágenes. No son iconos simulados.",
    }


def crear_boceto_desde_motivos(analisis_id: str, ids: list[str]) -> dict[str, Any]:
    data = ANALISIS_CACHE.get(analisis_id)
    if not data:
        raise ValueError("No se encuentra el análisis temporal. Vuelve a analizar las imágenes.")
    motivos = [m for m in data["motivos"] if m["id"] in set(ids)]
    if not motivos:
        raise ValueError("No hay motivos seleccionados.")
    # Composición sencilla inicial: roseta/marco con motivos pequeños y ramillete central.
    W, H = 1100, 820
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']
    chunks.append('<g fill="none" stroke="#111" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">')
    center = [(W/2, H*0.45), (W/2-120,H*0.50), (W/2+120,H*0.50), (W/2,H*0.28), (W/2,H*0.63)]
    ring = []
    for a in np.linspace(210, -30, max(8, min(20, len(motivos))), endpoint=True):
        rad = math.radians(a)
        ring.append((W/2 + math.cos(rad)*390, H*0.55 + math.sin(rad)*260))
    positions = center + ring
    for idx, m in enumerate(motivos[:len(positions)]):
        # Extrae paths internos del SVG del motivo.
        import re
        paths = re.findall(r'<path d="([^"]+)"', m["svg"])
        vb = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', m["svg"])
        mw, mh = (120, 120)
        if vb:
            mw, mh = float(vb.group(1)), float(vb.group(2))
        px, py = positions[idx]
        scale = 150 / max(mw, mh) if idx < 5 else 95 / max(mw, mh)
        chunks.append(f'<g transform="translate({px-mw*scale/2:.1f},{py-mh*scale/2:.1f}) scale({scale:.4f})">')
        for p in paths[:70]:
            chunks.append(f'<path d="{p}"/>')
        chunks.append('</g>')
    chunks.append('</g></svg>')
    svg = "\n".join(chunks)
    return {"ok": True, "svg": svg, "svg_data": _svg_data_url(svg), "motivos_usados": len(motivos)}
