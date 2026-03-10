import uuid
import streamlit as st
from db.sheets import get_ws, clear_cache

COLS_SERV = [
    "id", "fecha", "responsable", "hora", "cliente",
    "servicio", "patente", "estado", "detalle", "cargado_por",
]


def _parse_serv(r: dict) -> dict:
    return {
        "id":          str(r.get("id", "")),
        "fecha":       r.get("fecha", ""),
        "responsable": r.get("responsable", ""),
        "hora":        r.get("hora", ""),
        "cliente":     r.get("cliente", ""),
        "servicio":    r.get("servicio", ""),
        "patente":     r.get("patente", ""),
        "estado":      r.get("estado", "PENDIENTE"),
        "detalle":     r.get("detalle", ""),
        "cargado_por": r.get("cargado_por", ""),
    }


@st.cache_data(ttl=60)
def cargar_servicios() -> list:
    ws = get_ws("servicios_unificados")
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append(_parse_serv(r))
        except Exception:
            continue
    return result


def _init_servicios_ws():
    ws = get_ws("servicios_unificados")
    if not ws.get_all_values():
        ws.append_row(COLS_SERV)
        clear_cache()


def guardar_servicio(s: dict):
    ws = get_ws("servicios_unificados")
    if not ws.get_all_values():
        ws.append_row(COLS_SERV)
    ws.append_row([
        str(uuid.uuid4())[:8],
        s["fecha"], s["responsable"], s["hora"],
        s["cliente"], s["servicio"], s["patente"],
        s.get("estado", "PENDIENTE"), s.get("detalle", ""), s.get("cargado_por", ""),
    ])
    clear_cache()


def actualizar_estado_servicio(serv_id: str, nuevo_estado: str) -> bool:
    ws = get_ws("servicios_unificados")
    vals = ws.get_all_values()
    if not vals:
        return False
    headers = vals[0]
    try:
        estado_col = headers.index("estado") + 1
    except ValueError:
        return False
    for i, row in enumerate(vals[1:], start=2):
        if row and row[0] == serv_id:
            ws.update_cell(i, estado_col, nuevo_estado)
            clear_cache()
            return True
    return False


def eliminar_servicio(serv_id: str):
    ws = get_ws("servicios_unificados")
    vals = ws.get_all_values()
    if not vals:
        return
    for i, row in enumerate(vals[1:], start=2):
        if row and row[0] == serv_id:
            ws.delete_rows(i)
            clear_cache()
            return
