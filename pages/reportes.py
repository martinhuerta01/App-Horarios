from datetime import date
import pandas as pd
import streamlit as st

from config import MESES, EQUIPOS
from utils import decimal_a_hhmm
from db.empleados import cargar_empleados
from db.registros import cargar_registros
from db.servicios import cargar_servicios


def pagina_reporte_cruzado():
    st.markdown("### ⚡ Reporte cruzado — Horarios vs Servicios")
    st.caption("Compará las horas trabajadas de un técnico con la cantidad de servicios realizados por su equipo.")

    col1, col2, col3 = st.columns(3)
    with col1:
        mes_sel  = st.selectbox("Mes",  MESES, index=date.today().month - 1, key="rep_mes")
    with col2:
        anio_sel = st.selectbox("Año",  [2024, 2025, 2026, 2027], index=2, key="rep_anio")
    with col3:
        empleados   = cargar_empleados(solo_activos=False)
        nombres     = [e["nombre"] for e in empleados]
        tecnico_sel = st.selectbox("Técnico", nombres if nombres else ["—"])

    mes_num  = str(MESES.index(mes_sel) + 1).zfill(2)
    anio_str = str(anio_sel)
    prefijo  = f"{anio_str}-{mes_num}"

    emp_obj     = next((e for e in empleados if e["nombre"] == tecnico_sel), None)
    patente_tec = emp_obj["patente"] if emp_obj else ""

    equipo_tec = None
    for eq, pat in EQUIPOS.items():
        if pat.upper() == patente_tec.upper():
            equipo_tec = eq
            break

    # Datos — ambas listas ya cacheadas, sin llamadas extra a Sheets
    registros = [r for r in cargar_registros() if r["nombre"] == tecnico_sel and r["fecha"].startswith(prefijo)]
    servicios  = []
    if equipo_tec:
        servicios = [
            s for s in cargar_servicios()
            if s["responsable"] == equipo_tec
            and s["fecha"].startswith(prefijo)
            and s["estado"].upper() == "REALIZADO"
        ]

    st.markdown("---")
    if not registros:
        st.info(f"No hay registros de horario para {tecnico_sel} en {mes_sel} {anio_sel}.")

    total_horas    = sum(r["horas_trabajadas"] for r in registros)
    total_balance  = sum(r["diferencia"]       for r in registros)
    dias_trabajados = len(registros)
    total_servicios = len(servicios)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👷 Técnico",            tecnico_sel)
    m2.metric("🚗 Equipo",             equipo_tec or "No asignado")
    m3.metric("📅 Días trabajados",    dias_trabajados)
    m4.metric("⏱️ Horas trabajadas",   decimal_a_hhmm(total_horas))
    m5.metric("🔧 Servicios realizados", total_servicios)

    if dias_trabajados > 0 and total_servicios > 0:
        prom_serv_dia  = total_servicios / dias_trabajados
        prom_hs_serv   = total_horas / total_servicios
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Servicios / día promedio",   f"{prom_serv_dia:.1f}")
        c2.metric("⏱️ Horas / servicio promedio",  f"{prom_hs_serv:.1f}h")
        c3.metric("⚖️ Balance acumulado",          decimal_a_hhmm(total_balance))

    if registros:
        st.markdown("---")
        st.markdown("#### Detalle por día")
        servicios_por_dia = {}
        for s in servicios:
            servicios_por_dia[s["fecha"]] = servicios_por_dia.get(s["fecha"], 0) + 1

        df_cruzado = pd.DataFrame([{
            "Fecha":               r["fecha"],
            "Entrada":             r["hora_entrada"],
            "Salida":              r["hora_salida"],
            "Horas trabajadas":    decimal_a_hhmm(r["horas_trabajadas"]),
            "Balance":             decimal_a_hhmm(r["diferencia"]),
            "Servicios realizados": servicios_por_dia.get(r["fecha"], 0),
        } for r in sorted(registros, key=lambda x: x["fecha"])])
        st.dataframe(df_cruzado, use_container_width=True, hide_index=True)

    if not equipo_tec:
        st.warning(
            f"⚠️ {tecnico_sel} no tiene una patente asignada que coincida con los equipos "
            f"({', '.join(EQUIPOS.values())}). Actualizalo en Técnicos."
        )
