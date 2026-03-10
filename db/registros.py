import uuid
import streamlit as st
from db.sheets import get_ws, clear_cache

COLS_REG = [
    "id", "empleado_id", "nombre", "fecha", "hora_entrada", "hora_salida",
    "horas_trabajadas", "diferencia", "inicio_ruta", "fin_ruta", "cargado_por", "detalle",
]


def _parse_reg(r: dict) -> dict:
    return {
        "id":              str(r.get("id", "")),
        "empleado_id":     str(r.get("empleado_id", "")),
        "nombre":          r.get("nombre", ""),
        "fecha":           r.get("fecha", ""),
        "hora_entrada":    r.get("hora_entrada", ""),
        "hora_salida":     r.get("hora_salida", ""),
        "horas_trabajadas": float(r.get("horas_trabajadas", 0) or 0),
        "diferencia":      float(r.get("diferencia", 0) or 0),
        "inicio_ruta":     r.get("inicio_ruta", ""),
        "fin_ruta":        r.get("fin_ruta", ""),
        "cargado_por":     r.get("cargado_por", ""),
        "detalle":         r.get("detalle", ""),
    }


@st.cache_data(ttl=60)
def cargar_registros() -> list:
    ws = get_ws("registros")
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append(_parse_reg(r))
        except Exception:
            continue
    return result


def _init_registros_ws():
    ws = get_ws("registros")
    if not ws.get_all_values():
        ws.append_row(COLS_REG)
        clear_cache()


def guardar_registro(reg: dict) -> tuple[bool, str]:
    # Chequeo duplicado en memoria (sin llamada extra a Sheets)
    registros = cargar_registros()
    for r in registros:
        if r["empleado_id"] == reg["empleado_id"] and r["fecha"] == reg["fecha"]:
            return False, "Ya existe un registro para ese técnico en esa fecha."

    ws = get_ws("registros")
    if not ws.get_all_values():
        ws.append_row(COLS_REG)

    ws.append_row([
        str(uuid.uuid4())[:8],
        reg["empleado_id"], reg["nombre"], reg["fecha"],
        reg["hora_entrada"], reg["hora_salida"],
        reg["horas_trabajadas"], reg["diferencia"],
        reg.get("inicio_ruta", ""), reg.get("fin_ruta", ""),
        reg.get("cargado_por", ""), reg.get("detalle", ""),
    ])
    clear_cache()
    return True, "OK"


def actualizar_registro(reg_id: str, reg: dict) -> bool:
    ws = get_ws("registros")
    vals = ws.get_all_values()
    if not vals:
        return False
    for i, row in enumerate(vals[1:], start=2):
        if row and row[0] == reg_id:
            ws.update(f"A{i}:L{i}", [[
                reg_id, reg["empleado_id"], reg["nombre"], reg["fecha"],
                reg["hora_entrada"], reg["hora_salida"],
                reg["horas_trabajadas"], reg["diferencia"],
                reg.get("inicio_ruta", ""), reg.get("fin_ruta", ""),
                reg.get("cargado_por", ""), reg.get("detalle", ""),
            ]])
            clear_cache()
            return True
    return False


def eliminar_registro(reg_id: str):
    ws = get_ws("registros")
    vals = ws.get_all_values()
    if not vals:
        return
    for i, row in enumerate(vals[1:], start=2):
        if row and row[0] == reg_id:
            ws.delete_rows(i)
            clear_cache()
            return
