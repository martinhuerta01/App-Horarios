import uuid
import streamlit as st
from db.sheets import get_ws, clear_cache

COLS_EMP = ["id", "nombre", "activo", "telefono", "dni", "zona", "vehiculo", "patente", "observaciones"]


def _parse_emp(r: dict) -> dict:
    return {
        "id":            str(r.get("id", "")),
        "nombre":        r.get("nombre", ""),
        "activo":        str(r.get("activo", "1")) == "1",
        "telefono":      r.get("telefono", ""),
        "dni":           r.get("dni", ""),
        "zona":          r.get("zona", ""),
        "vehiculo":      r.get("vehiculo", ""),
        "patente":       r.get("patente", ""),
        "observaciones": r.get("observaciones", ""),
    }


@st.cache_data(ttl=120)
def cargar_empleados(solo_activos: bool = False) -> list:
    ws = get_ws("empleados")
    records = ws.get_all_records()
    empleados = [_parse_emp(r) for r in records]
    if solo_activos:
        empleados = [e for e in empleados if e["activo"]]
    return sorted(empleados, key=lambda x: x["nombre"])


def _init_empleados_ws():
    ws = get_ws("empleados")
    if not ws.get_all_values():
        ws.append_row(COLS_EMP)
        for nombre in ["Maxi", "Sergio", "Hugo", "Lautaro"]:
            ws.append_row([str(uuid.uuid4())[:8], nombre, "1", "", "", "", "", "", ""])
        clear_cache()


def guardar_empleado_nuevo(emp: dict):
    ws = get_ws("empleados")
    if not ws.get_all_values():
        ws.append_row(COLS_EMP)
    ws.append_row([
        str(uuid.uuid4())[:8],
        emp.get("nombre", ""),
        "1" if emp.get("activo", True) else "0",
        emp.get("telefono", ""), emp.get("dni", ""), emp.get("zona", ""),
        emp.get("vehiculo", ""), emp.get("patente", ""), emp.get("observaciones", ""),
    ])
    clear_cache()


def actualizar_empleado(emp_id: str, emp: dict):
    ws = get_ws("empleados")
    vals = ws.get_all_values()
    if not vals:
        return
    for i, row in enumerate(vals[1:], start=2):
        if row and row[0] == emp_id:
            ws.update(f"A{i}:I{i}", [[
                emp_id, emp.get("nombre", ""),
                "1" if emp.get("activo", True) else "0",
                emp.get("telefono", ""), emp.get("dni", ""), emp.get("zona", ""),
                emp.get("vehiculo", ""), emp.get("patente", ""), emp.get("observaciones", ""),
            ]])
            clear_cache()
            return
