from datetime import date
import pandas as pd
import streamlit as st

from config import RESPONSABLES, ESTADOS_SERVICIO, TIPOS_SERVICIO
from db.servicios import cargar_servicios, guardar_servicio, actualizar_estado_servicio, eliminar_servicio


def pagina_serv_cargar():
    st.markdown("### ➕ Cargar servicio")
    with st.form("form_serv_nuevo", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_fecha       = st.date_input("Fecha", value=date.today())
        with col2:
            s_responsable = st.selectbox("Responsable", RESPONSABLES)
        with col3:
            s_hora        = st.text_input("Hora (HH:MM)", placeholder="10:00")

        col4, col5 = st.columns(2)
        with col4:
            s_cliente  = st.text_input("Cliente *", placeholder="QUILMES DISTRIBUIDORES")
        with col5:
            s_servicio = st.selectbox("Servicio", TIPOS_SERVICIO)

        col6, col7 = st.columns(2)
        with col6:
            s_patente = st.text_input("Patente", placeholder="HQT470 / KWN846")
        with col7:
            s_estado = st.selectbox("Estado", ESTADOS_SERVICIO)

        s_detalle = st.text_area("Detalle", placeholder="GPS, cámara, corte corriente, dirección, contacto...")

        if st.form_submit_button("💾 Guardar servicio", use_container_width=True):
            if not s_cliente:
                st.error("El cliente es obligatorio.")
            else:
                guardar_servicio({
                    "fecha":       s_fecha.strftime("%Y-%m-%d"),
                    "responsable": s_responsable,
                    "hora":        s_hora.strip(),
                    "cliente":     s_cliente,
                    "servicio":    s_servicio,
                    "patente":     s_patente,
                    "estado":      s_estado,
                    "detalle":     s_detalle,
                    "cargado_por": st.session_state.get("usuario", ""),
                })
                st.success("✅ Servicio guardado.")


def pagina_serv_lista():
    st.markdown("### 📋 Detalle / Lista de servicios")
    servicios = cargar_servicios()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filtro_resp  = st.selectbox("Responsable", ["Todos"] + RESPONSABLES)
    with col2:
        filtro_desde = st.date_input("Desde", value=date.today().replace(day=1))
    with col3:
        filtro_hasta = st.date_input("Hasta", value=date.today())
    with col4:
        filtro_estado = st.selectbox("Estado", ["Todos"] + ESTADOS_SERVICIO)

    filtro_cliente = st.text_input("Buscar cliente", placeholder="Escribí parte del nombre...")

    filtrados = servicios
    if filtro_resp   != "Todos":
        filtrados = [s for s in filtrados if s["responsable"] == filtro_resp]
    if filtro_estado != "Todos":
        filtrados = [s for s in filtrados if s["estado"].upper() == filtro_estado]
    if filtro_cliente:
        filtrados = [s for s in filtrados if filtro_cliente.lower() in s["cliente"].lower()]
    filtrados = [
        s for s in filtrados
        if filtro_desde.strftime("%Y-%m-%d") <= s["fecha"] <= filtro_hasta.strftime("%Y-%m-%d")
    ]
    filtrados = sorted(filtrados, key=lambda x: (x["fecha"], x["hora"]), reverse=True)

    if not filtrados:
        st.info("No hay servicios con ese filtro.")
        return

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total",           len(filtrados))
    m2.metric("🟢 Realizados",   sum(1 for s in filtrados if s["estado"].upper() == "REALIZADO"))
    m3.metric("🔵 Confirmados",  sum(1 for s in filtrados if s["estado"].upper() == "CONFIRMADO"))
    m4.metric("🟡 Pendientes",   sum(1 for s in filtrados if s["estado"].upper() == "PENDIENTE"))
    m5.metric("🔴 Suspendidos",  sum(1 for s in filtrados if s["estado"].upper() in ["SUSPENDIDO", "REPROGRAMADO"]))

    st.markdown("---")
    st.caption("Cambiá el estado directamente en la tabla y hacé click en Guardar cambios.")

    df_edit = pd.DataFrame([{
        "id":          s["id"],
        "Fecha":       s["fecha"],
        "Responsable": s["responsable"],
        "Hora":        s["hora"],
        "Cliente":     s["cliente"],
        "Servicio":    s["servicio"],
        "Patente":     s["patente"],
        "Estado":      s["estado"],
        "Detalle":     s["detalle"],
    } for s in filtrados])

    edited_df = st.data_editor(
        df_edit.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Estado":      st.column_config.SelectboxColumn("Estado", options=ESTADOS_SERVICIO, required=True),
            "Fecha":       st.column_config.TextColumn("Fecha",       disabled=True),
            "Responsable": st.column_config.TextColumn("Responsable", disabled=True),
            "Hora":        st.column_config.TextColumn("Hora",        disabled=True),
            "Cliente":     st.column_config.TextColumn("Cliente",     disabled=True),
            "Servicio":    st.column_config.TextColumn("Servicio",    disabled=True),
            "Patente":     st.column_config.TextColumn("Patente",     disabled=True),
            "Detalle":     st.column_config.TextColumn("Detalle",     disabled=True),
        },
    )

    if st.button("💾 Guardar cambios de estado", use_container_width=True):
        cambios = 0
        for i, row in edited_df.iterrows():
            serv_id = df_edit.iloc[i]["id"]
            if row["Estado"] != df_edit.iloc[i]["Estado"]:
                actualizar_estado_servicio(serv_id, row["Estado"])
                cambios += 1
        if cambios > 0:
            st.success(f"✅ {cambios} estado(s) actualizado(s).")
            st.rerun()
        else:
            st.info("No hubo cambios.")

    st.markdown("---")
    st.markdown("**Eliminar un servicio**")
    opciones_del = [f"{s['fecha']} | {s['responsable']} | {s['hora']} | {s['cliente']}" for s in filtrados]
    sel_del      = st.selectbox("Seleccioná un servicio", opciones_del, key="del_serv")
    if st.button("🗑️ Eliminar seleccionado", key="btn_del_serv"):
        eliminar_servicio(filtrados[opciones_del.index(sel_del)]["id"])
        st.success("Servicio eliminado.")
        st.rerun()
