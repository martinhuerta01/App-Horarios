"""
Panel de Control — app.py
Punto de entrada único. Solo se encarga de:
  1. CSS global
  2. Login / logout
  3. Sidebar con módulos
  4. Routing a las páginas
Para agregar un nuevo módulo: editá config.py (MODULOS) y creá su página en pages/.
"""
import streamlit as st

from config import MODULOS
from db.empleados  import _init_empleados_ws
from db.registros  import _init_registros_ws
from db.servicios  import _init_servicios_ws
from db.stock      import _init_stock_ws
from db.usuarios   import validar_usuario

# ── Pages ──────────────────────────────────────────────────────────
from modules.horarios  import (
    pagina_registro, pagina_historial, pagina_resumen,
    pagina_estadisticas, pagina_tecnicos,
)
from modules.servicios import pagina_serv_cargar, pagina_serv_lista
from modules.stock     import (
    pagina_stock_actual, pagina_stock_entrada,
    pagina_stock_salida, pagina_stock_productos,
)
from modules.reportes  import pagina_reporte_cruzado

# Mapa de rutas — agregá acá cuando crees nuevas páginas
RUTAS = {
    "registro":        pagina_registro,
    "historial":       pagina_historial,
    "resumen":         pagina_resumen,
    "estadisticas":    pagina_estadisticas,
    "tecnicos":        pagina_tecnicos,
    "serv_cargar":     pagina_serv_cargar,
    "serv_lista":      pagina_serv_lista,
    "stock_actual":    pagina_stock_actual,
    "stock_entrada":   pagina_stock_entrada,
    "stock_salida":    pagina_stock_salida,
    "stock_productos": pagina_stock_productos,
    "reporte_cruzado": pagina_reporte_cruzado,
}

# ══════════════════════════════════════════════════════════════════
# Config & CSS
# ══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Panel de Control", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }
code, .mono { font-family: 'DM Mono', monospace; }

.stApp { background: #f1f3f6; }
[data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e6ea; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e6ea;
    border-radius: 12px;
    padding: 16px;
}
[data-testid="metric-container"] label { color: #6b7280 !important; font-size: 12px !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #1e3a8a !important; font-size: 22px !important; font-weight: 700 !important;
}

.stButton > button {
    background: #1e3a8a !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { background: #2745a7 !important; transform: translateY(-1px); }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stTextArea textarea {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #111827 !important;
    border-radius: 8px !important;
}

.stTabs [data-baseweb="tab-list"] { background: #e5e7eb; border-radius: 10px; padding: 4px; gap: 4px; }
.stTabs [data-baseweb="tab"] { color: #6b7280 !important; border-radius: 8px !important; font-weight: 500; }
.stTabs [aria-selected="true"] { background: #1e3a8a !important; color: white !important; }

[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
.stDataFrame { background: #ffffff !important; }

h1, h2, h3 { color: #111827 !important; }
p, label { color: #374151 !important; }
hr { border-color: #e2e6ea !important; }

.stSuccess { background: #f0fdf4 !important; border: 1px solid #86efac !important; color: #166534 !important; border-radius: 8px !important; }
.stError   { background: #fef2f2 !important; border: 1px solid #fca5a5 !important; color: #991b1b !important; border-radius: 8px !important; }
.stWarning { background: #fffbeb !important; border: 1px solid #fcd34d !important; color: #92400e !important; border-radius: 8px !important; }

[data-testid="stSidebar"] .stButton > button {
    border-radius: 6px !important;
    text-align: left !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# Login
# ══════════════════════════════════════════════════════════════════
def pagina_login():
    st.markdown("""
    <div style='text-align:center; padding:60px 0 20px'>
        <span style='font-size:48px'>⚙️</span>
        <h1 style='font-size:28px; font-weight:700; margin:8px 0 4px'>Panel de Control</h1>
        <p style='color:#6b7280; font-size:14px'>Ingresá para continuar</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            usuario  = st.selectbox("Usuario", ["Alejo", "Martin"])
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if validar_usuario(usuario, password):
                    st.session_state["usuario"] = usuario
                    st.session_state["pagina"]  = "registro"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")


# ══════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════
def render_sidebar():
    usuario = st.session_state.get("usuario", "")
    pagina  = st.session_state.get("pagina", "registro")

    # Módulo activo (para auto-abrir el panel correcto)
    modulo_activo = MODULOS[0]["id"]
    for mod in MODULOS:
        if any(pagina == sub_key for sub_key, _ in mod["subs"]):
            modulo_activo = mod["id"]
            break

    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 4px 12px; border-bottom:1px solid #f0f0f0; margin-bottom:12px'>
            <div style='font-size:18px; font-weight:700; color:#111827'>⚙️ Panel de Control</div>
            <div style='font-size:12px; color:#9ca3af; margin-top:2px'>Usuario: {usuario}</div>
        </div>
        """, unsafe_allow_html=True)

        for mod in MODULOS:
            is_open = st.session_state.get(f"mod_open_{mod['id']}", mod["id"] == modulo_activo)
            color   = mod["color"]
            arrow   = "▲" if is_open else "▼"
            bg      = color if is_open else "#f3f4f6"
            txt     = "#ffffff" if is_open else "#111827"

            st.markdown(f"""
            <style>
            div[data-testid="stSidebar"] button[aria-label="{mod['icon']}  {mod['label']}  {arrow}"] {{
                background: {bg} !important; color: {txt} !important;
                border: none !important; font-weight: 700 !important;
                font-size: 13px !important; text-align: left !important;
                padding: 8px 12px !important; margin-bottom: 2px !important;
            }}
            </style>
            """, unsafe_allow_html=True)

            if st.button(f"{mod['icon']}  {mod['label']}  {arrow}", key=f"toggle_{mod['id']}", use_container_width=True):
                # Sólo cambia el estado del acordeón, sin rerun extra si ya está en ese módulo
                st.session_state[f"mod_open_{mod['id']}"] = not is_open
                st.rerun()

            if is_open:
                for sub_key, sub_label in mod["subs"]:
                    activo = pagina == sub_key
                    if activo:
                        st.markdown(f"""
                        <style>
                        div[data-testid="stSidebar"] button[aria-label="{sub_label}"] {{
                            background: {color}18 !important; color: {color} !important;
                            font-weight: 600 !important; border-left: 3px solid {color} !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    _, c_btn = st.columns([0.08, 0.92])
                    with c_btn:
                        if st.button(sub_label, key=f"nav_{sub_key}", use_container_width=True):
                            st.session_state["pagina"] = sub_key
                            st.rerun()

                st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state["usuario"] = None
            st.session_state["pagina"]  = "registro"
            st.rerun()


# ══════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════
def main():
    st.session_state.setdefault("usuario", None)
    st.session_state.setdefault("pagina",  "registro")

    if not st.session_state["usuario"]:
        pagina_login()
        return

    # Inicializar hojas solo una vez (rápido si ya existen)
    _init_empleados_ws()
    _init_registros_ws()
    _init_servicios_ws()
    _init_stock_ws()

    render_sidebar()

    fn = RUTAS.get(st.session_state["pagina"])
    if fn:
        fn()
    else:
        st.error(f"Página '{st.session_state['pagina']}' no encontrada.")


if __name__ == "__main__":
    main()
