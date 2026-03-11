from datetime import date
import pandas as pd
import streamlit as st

from config import UBICACIONES_STOCK, CATEGORIAS_STOCK
from db.stock import cargar_stock, cargar_movimientos, guardar_producto, registrar_movimiento


def pagina_stock_actual():
    st.markdown("### 📊 Stock actual")
    productos = cargar_stock()
    if not productos:
        st.info("No hay productos cargados. Agregalos en la sección Productos.")
        return

    df = pd.DataFrame([{
        "Código":    p["codigo"],
        "Producto":  p["producto"],
        "Categoría": p["categoria"],
        "Stock":     p["stock_actual"],
        "Obs":       p["control_observacion"],
    } for p in productos])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.metric("Total unidades en stock", sum(p["stock_actual"] for p in productos))


def pagina_stock_entrada():
    st.markdown("### 📥 Registrar entrada de stock")
    productos = cargar_stock()
    if not productos:
        st.warning("No hay productos. Agregalos primero en Productos.")
        return

    prod_map = {f"{p['codigo']} — {p['producto']}": p for p in productos}
    with st.form("form_entrada", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prod_sel  = st.selectbox("Producto", list(prod_map.keys()))
        with col2:
            cantidad  = st.number_input("Cantidad", min_value=1, value=1)
        col3, col4 = st.columns(2)
        with col3:
            ubicacion = st.selectbox("Ubicación destino", UBICACIONES_STOCK)
        with col4:
            fecha_mov = st.date_input("Fecha", value=date.today())
        obs = st.text_input("Observación", placeholder="Proveedor, nro de remito, etc.")

        if st.form_submit_button("💾 Registrar entrada", use_container_width=True):
            p = prod_map[prod_sel]
            registrar_movimiento({
                "tipo":        "ENTRADA",
                "producto_id": p["id"],
                "producto":    p["producto"],
                "cantidad":    cantidad,
                "ubicacion":   ubicacion,
                "fecha":       fecha_mov.strftime("%Y-%m-%d"),
                "cargado_por": st.session_state.get("usuario", ""),
                "observacion": obs,
            })
            st.success(f"✅ Entrada de {cantidad} unidades registrada. Stock actualizado.")


def pagina_stock_salida():
    st.markdown("### 📤 Registrar salida de stock")
    productos = cargar_stock()
    if not productos:
        st.warning("No hay productos. Agregalos primero en Productos.")
        return

    prod_map = {f"{p['codigo']} — {p['producto']} (stock: {p['stock_actual']})": p for p in productos}
    with st.form("form_salida", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prod_sel  = st.selectbox("Producto", list(prod_map.keys()))
        with col2:
            cantidad  = st.number_input("Cantidad", min_value=1, value=1)
        col3, col4 = st.columns(2)
        with col3:
            ubicacion = st.selectbox("Destino", UBICACIONES_STOCK)
        with col4:
            fecha_mov = st.date_input("Fecha", value=date.today())
        obs = st.text_input("Observación", placeholder="Número de servicio, cliente, etc.")

        if st.form_submit_button("💾 Registrar salida", use_container_width=True):
            p = prod_map[prod_sel]
            if cantidad > p["stock_actual"]:
                st.error(f"Stock insuficiente. Stock actual: {p['stock_actual']}")
            else:
                registrar_movimiento({
                    "tipo":        "SALIDA",
                    "producto_id": p["id"],
                    "producto":    p["producto"],
                    "cantidad":    cantidad,
                    "ubicacion":   ubicacion,
                    "fecha":       fecha_mov.strftime("%Y-%m-%d"),
                    "cargado_por": st.session_state.get("usuario", ""),
                    "observacion": obs,
                })
                st.success(f"✅ Salida de {cantidad} unidades registrada. Stock actualizado.")


def pagina_stock_productos():
    st.markdown("### ⚙️ Gestión de productos")
    tab1, tab2 = st.tabs(["📋 Ver productos", "➕ Nuevo producto"])

    with tab1:
        productos = cargar_stock()
        if not productos:
            st.info("No hay productos cargados.")
        else:
            df = pd.DataFrame([{
                "Código":      p["codigo"],
                "Producto":    p["producto"],
                "Categoría":   p["categoria"],
                "Stock":       p["stock_actual"],
                "Observación": p["control_observacion"],
            } for p in productos])
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("**Historial de movimientos**")
        movimientos = cargar_movimientos()
        if movimientos:
            df_mov = pd.DataFrame([{
                "Tipo":        m["tipo"],
                "Producto":    m["producto"],
                "Cantidad":    m["cantidad"],
                "Ubicación":   m["ubicacion"],
                "Fecha":       m["fecha"],
                "Cargado por": m["cargado_por"],
                "Observación": m["observacion"],
            } for m in sorted(movimientos, key=lambda x: x["fecha"], reverse=True)])
            st.dataframe(df_mov, use_container_width=True, hide_index=True)

    with tab2:
        with st.form("form_nuevo_prod", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_codigo = st.text_input("Código *",   placeholder="D01 / I05")
                p_nombre = st.text_input("Producto *",  placeholder="TRAX S40 (NUEVOS)")
            with col2:
                p_cat   = st.selectbox("Categoría", CATEGORIAS_STOCK)
                p_stock = st.number_input("Stock inicial", min_value=0, value=0)
            p_obs = st.text_input("Observación / Control")
            if st.form_submit_button("💾 Agregar producto", use_container_width=True):
                if not p_codigo or not p_nombre:
                    st.error("Código y producto son obligatorios.")
                else:
                    guardar_producto({
                        "codigo": p_codigo, "producto": p_nombre,
                        "categoria": p_cat, "stock_actual": p_stock,
                        "control_observacion": p_obs,
                    })
                    st.success(f"✅ Producto '{p_nombre}' agregado.")
                    st.rerun()
