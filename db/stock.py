import uuid
import streamlit as st
from db.sheets import get_ws, clear_cache

COLS_STOCK = ["id", "codigo", "producto", "categoria", "stock_actual", "control_observacion"]
COLS_MOV   = ["id", "tipo", "producto_id", "producto", "cantidad", "ubicacion", "fecha", "cargado_por", "observacion"]


def _parse_prod(r: dict) -> dict:
    return {
        "id":                 str(r.get("id", "")),
        "codigo":             r.get("codigo", ""),
        "producto":           r.get("producto", ""),
        "categoria":          r.get("categoria", ""),
        "stock_actual":       int(r.get("stock_actual", 0) or 0),
        "control_observacion": r.get("control_observacion", ""),
    }


def _parse_mov(r: dict) -> dict:
    return {
        "id":          str(r.get("id", "")),
        "tipo":        r.get("tipo", ""),
        "producto_id": str(r.get("producto_id", "")),
        "producto":    r.get("producto", ""),
        "cantidad":    int(r.get("cantidad", 0) or 0),
        "ubicacion":   r.get("ubicacion", ""),
        "fecha":       r.get("fecha", ""),
        "cargado_por": r.get("cargado_por", ""),
        "observacion": r.get("observacion", ""),
    }


@st.cache_data(ttl=60)
def cargar_stock() -> list:
    ws = get_ws("stock_productos")
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append(_parse_prod(r))
        except Exception:
            continue
    return result


@st.cache_data(ttl=60)
def cargar_movimientos() -> list:
    ws = get_ws("stock_movimientos")
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append(_parse_mov(r))
        except Exception:
            continue
    return result


def _init_stock_ws():
    ws_p = get_ws("stock_productos")
    if not ws_p.get_all_values():
        ws_p.append_row(COLS_STOCK)
    ws_m = get_ws("stock_movimientos")
    if not ws_m.get_all_values():
        ws_m.append_row(COLS_MOV)
    clear_cache()


def guardar_producto(p: dict):
    ws = get_ws("stock_productos")
    if not ws.get_all_values():
        ws.append_row(COLS_STOCK)
    ws.append_row([
        str(uuid.uuid4())[:8], p["codigo"], p["producto"],
        p.get("categoria", ""), p.get("stock_actual", 0), p.get("control_observacion", ""),
    ])
    clear_cache()


def registrar_movimiento(mov: dict):
    """Registra el movimiento y actualiza el stock_actual en una sola sesión de red."""
    ws_m = get_ws("stock_movimientos")
    if not ws_m.get_all_values():
        ws_m.append_row(COLS_MOV)
    ws_m.append_row([
        str(uuid.uuid4())[:8], mov["tipo"], mov["producto_id"], mov["producto"],
        mov["cantidad"], mov["ubicacion"], mov["fecha"],
        mov.get("cargado_por", ""), mov.get("observacion", ""),
    ])

    ws_p = get_ws("stock_productos")
    vals = ws_p.get_all_values()
    if not vals:
        clear_cache()
        return
    headers = vals[0]
    try:
        stock_col = headers.index("stock_actual") + 1
    except ValueError:
        clear_cache()
        return
    for i, row in enumerate(vals[1:], start=2):
        if row and row[0] == mov["producto_id"]:
            try:
                actual = int(row[stock_col - 1] or 0)
            except Exception:
                actual = 0
            delta = mov["cantidad"] if mov["tipo"] == "ENTRADA" else -mov["cantidad"]
            ws_p.update_cell(i, stock_col, actual + delta)
            break
    clear_cache()
