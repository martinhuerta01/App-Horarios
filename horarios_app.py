import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime, timedelta
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import io
import uuid

# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
JORNADA_BASE = 8.0  # horas

st.set_page_config(page_title="Control de Horarios", page_icon="🕐", layout="wide")

# ══════════════════════════════════════════════════════════════════
# CSS — mismo estilo que app de gastos
# ══════════════════════════════════════════════════════════════════
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
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #1e3a8a !important; font-size: 22px !important; font-weight: 700 !important; }

[data-testid="stSidebar"] .stButton > button {
    background: #1f2937 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #374151 !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #1e3a8a !important;
    color: white !important;
    border: none !important;
}

.stButton > button {
    background: #1e3a8a !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { background: #2745a7 !important; transform: translateY(-1px); }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input {
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
.stError { background: #fef2f2 !important; border: 1px solid #fca5a5 !important; color: #991b1b !important; border-radius: 8px !important; }
.stWarning { background: #fffbeb !important; border: 1px solid #fcd34d !important; color: #92400e !important; border-radius: 8px !important; }

.card {
    background: #ffffff;
    border: 1px solid #e2e6ea;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.badge-blue {
    background: #eff6ff;
    color: #1e40af;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.badge-green {
    background: #f0fdf4;
    color: #166534;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.badge-red {
    background: #fef2f2;
    color: #991b1b;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(dict(creds_dict), scopes=SCOPES)
    client = gspread.authorize(creds)
    SHEET_ID = st.secrets["sheet_id"]
    return client.open_by_key(SHEET_ID)

def get_ws(name: str):
    sh = get_sheet()
    try:
        return sh.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=2000, cols=20)
        return ws


# ══════════════════════════════════════════════════════════════════
# DATOS: USUARIOS
# ══════════════════════════════════════════════════════════════════
def cargar_usuarios() -> dict:
    ws = get_ws("usuarios")
    vals = ws.get_all_values()
    if not vals:
        default = {"Alejo": "1234", "Martin": "1234"}
        guardar_usuarios(default)
        return default
    return {r[0]: r[1] for r in vals if len(r) >= 2 and r[0]}

def guardar_usuarios(users: dict):
    ws = get_ws("usuarios")
    ws.clear()
    ws.append_rows([[u, p] for u, p in users.items()])
    st.cache_data.clear()

def validar_usuario(usuario: str, password: str) -> bool:
    return cargar_usuarios().get(usuario) == password


# ══════════════════════════════════════════════════════════════════
# DATOS: EMPLEADOS
# ══════════════════════════════════════════════════════════════════
COLS_EMP = ["id", "nombre", "activo", "telefono", "dni", "zona", "vehiculo", "patente", "observaciones"]

@st.cache_data(ttl=30)
def cargar_empleados(solo_activos=False) -> list:
    ws = get_ws("empleados")
    records = ws.get_all_records()
    empleados = []
    for r in records:
        emp = {
            "id": str(r.get("id", "")),
            "nombre": r.get("nombre", ""),
            "activo": str(r.get("activo", "1")) == "1",
            "telefono": r.get("telefono", ""),
            "dni": r.get("dni", ""),
            "zona": r.get("zona", ""),
            "vehiculo": r.get("vehiculo", ""),
            "patente": r.get("patente", ""),
            "observaciones": r.get("observaciones", ""),
        }
        empleados.append(emp)
    if solo_activos:
        empleados = [e for e in empleados if e["activo"]]
    return sorted(empleados, key=lambda x: x["nombre"])

@st.cache_resource
def _init_empleados_ws():
    ws = get_ws("empleados")
    _ensure_headers(ws, COLS_EMP)

def guardar_empleado_nuevo(emp: dict):
    ws = get_ws("empleados")
    if not ws.get_all_values():
        ws.append_row(COLS_EMP)
    ws.append_row([
        str(uuid.uuid4())[:8],
        emp.get("nombre", ""),
        "1" if emp.get("activo", True) else "0",
        emp.get("telefono", ""),
        emp.get("dni", ""),
        emp.get("zona", ""),
        emp.get("vehiculo", ""),
        emp.get("patente", ""),
        emp.get("observaciones", ""),
    ])
    st.cache_data.clear()

def actualizar_empleado(emp_id: str, emp: dict):
    ws = get_ws("empleados")
    vals = ws.get_all_values()
    if not vals:
        return
    headers = vals[0]
    id_col = headers.index("id") + 1
    for i, row in enumerate(vals[1:], start=2):
        if len(row) > 0 and row[0] == emp_id:
            ws.update(f"A{i}:I{i}", [[
                emp_id,
                emp.get("nombre", ""),
                "1" if emp.get("activo", True) else "0",
                emp.get("telefono", ""),
                emp.get("dni", ""),
                emp.get("zona", ""),
                emp.get("vehiculo", ""),
                emp.get("patente", ""),
                emp.get("observaciones", ""),
            ]])
            st.cache_data.clear()
            return


# ══════════════════════════════════════════════════════════════════
# DATOS: REGISTROS
# ══════════════════════════════════════════════════════════════════
COLS_REG = ["id", "empleado_id", "nombre", "fecha", "hora_entrada", "hora_salida", "horas_trabajadas", "diferencia", "inicio_ruta", "fin_ruta"]

@st.cache_data(ttl=10)
def cargar_registros() -> list:
    ws = get_ws("registros")
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append({
                "id": str(r.get("id", "")),
                "empleado_id": str(r.get("empleado_id", "")),
                "nombre": r.get("nombre", ""),
                "fecha": r.get("fecha", ""),
                "hora_entrada": r.get("hora_entrada", ""),
                "hora_salida": r.get("hora_salida", ""),
                "horas_trabajadas": float(r.get("horas_trabajadas", 0) or 0),
                "diferencia": float(r.get("diferencia", 0) or 0),
                "inicio_ruta": r.get("inicio_ruta", ""),
                "fin_ruta": r.get("fin_ruta", ""),
            })
        except Exception:
            continue
    return result

def _ensure_headers(ws, cols: list):
    """Agrega encabezados faltantes en una sola llamada a la API."""
    vals = ws.get_all_values()
    if not vals:
        ws.append_row(cols)
        return
    existing = vals[0]
    missing = [c for c in cols if c not in existing]
    if missing:
        new_row = existing + missing
        ws.update("1:1", [new_row])

@st.cache_resource
def _init_registros_ws():
    ws = get_ws("registros")
    _ensure_headers(ws, COLS_REG)

def guardar_registro(reg: dict):
    ws = get_ws("registros")
    if not ws.get_all_values():
        ws.append_row(COLS_REG)
    # Verificar duplicado (mismo empleado_id + fecha)
    registros = cargar_registros()
    for r in registros:
        if r["empleado_id"] == reg["empleado_id"] and r["fecha"] == reg["fecha"]:
            return False, "Ya existe un registro para ese técnico en esa fecha."
    ws.append_row([
        str(uuid.uuid4())[:8],
        reg["empleado_id"],
        reg["nombre"],
        reg["fecha"],
        reg["hora_entrada"],
        reg["hora_salida"],
        reg["horas_trabajadas"],
        reg["diferencia"],
        reg.get("inicio_ruta", ""),
        reg.get("fin_ruta", ""),
    ])
    st.cache_data.clear()
    st.cache_resource.clear()
    return True, "OK"

def actualizar_registro(reg_id: str, reg: dict):
    ws = get_ws("registros")
    vals = ws.get_all_values()
    if not vals:
        return False
    for i, row in enumerate(vals[1:], start=2):
        if len(row) > 0 and row[0] == reg_id:
            ws.update(f"A{i}:J{i}", [[
                reg_id,
                reg["empleado_id"],
                reg["nombre"],
                reg["fecha"],
                reg["hora_entrada"],
                reg["hora_salida"],
                reg["horas_trabajadas"],
                reg["diferencia"],
                reg.get("inicio_ruta", ""),
                reg.get("fin_ruta", ""),
            ]])
            st.cache_data.clear()
            return True
    return False

def eliminar_registro(reg_id: str):
    ws = get_ws("registros")
    vals = ws.get_all_values()
    if not vals:
        return
    for i, row in enumerate(vals[1:], start=2):
        if len(row) > 0 and row[0] == reg_id:
            ws.delete_rows(i)
            st.cache_data.clear()
            return


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def decimal_a_hhmm(val: float) -> str:
    neg = val < 0
    v = abs(val)
    h = int(v)
    m = int(round((v - h) * 60))
    if m == 60:
        h += 1
        m = 0
    s = f"{h}h {str(m).zfill(2)}m"
    return f"-{s}" if neg else s

def parse_hora(h: str) -> datetime:
    return datetime.strptime(h.strip(), "%H:%M")

def calcular_horas(entrada: str, salida: str):
    h_ent = parse_hora(entrada)
    h_sal = parse_hora(salida)
    if h_sal <= h_ent:
        return None, None
    diff = h_sal - h_ent
    trabajado = diff.total_seconds() / 3600
    diferencia = trabajado - JORNADA_BASE
    return trabajado, diferencia

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]


# ══════════════════════════════════════════════════════════════════
# PÁGINA: LOGIN
# ══════════════════════════════════════════════════════════════════
def pagina_login():
    st.markdown("""
    <div style='text-align:center; padding: 60px 0 20px'>
        <span style='font-size:48px'>🕐</span>
        <h1 style='font-size:28px; font-weight:700; margin:8px 0 4px'>Control de Horarios</h1>
        <p style='color:#6b7280; font-size:14px'>Ingresá para continuar</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.selectbox("Usuario", ["Alejo", "Martin"])
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)
            if submitted:
                if validar_usuario(usuario, password):
                    st.session_state["usuario"] = usuario
                    st.session_state["pagina"] = "registro"
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")


# ══════════════════════════════════════════════════════════════════
# PÁGINA: REGISTRO
# ══════════════════════════════════════════════════════════════════
def pagina_registro():
    st.markdown("### ➕ Cargar jornada")

    empleados = cargar_empleados(solo_activos=True)
    if not empleados:
        st.warning("No hay técnicos activos. Cargalos en la pestaña Técnicos.")
        return

    nombres = [e["nombre"] for e in empleados]
    emp_map = {e["nombre"]: e["id"] for e in empleados}

    col1, col2 = st.columns(2)
    with col1:
        tecnico = st.selectbox("Técnico", nombres)
    with col2:
        fecha = st.date_input("Fecha", value=date.today())

    col3, col4 = st.columns(2)
    with col3:
        entrada = st.text_input("Hora entrada (HH:MM)", placeholder="08:00")
    with col4:
        salida = st.text_input("Hora salida (HH:MM)", placeholder="16:00")

    col5, col6 = st.columns(2)
    with col5:
        inicio_ruta = st.text_input("Inicio de ruta", placeholder="Casa / Oficina / Depósito")
    with col6:
        fin_ruta = st.text_input("Fin de ruta", placeholder="Casa / Oficina / Depósito")

    if st.button("💾 Guardar registro", use_container_width=True):
        if not entrada or not salida:
            st.error("Completá la hora de entrada y salida.")
        else:
            try:
                trabajado, diferencia = calcular_horas(entrada, salida)
                if trabajado is None:
                    st.error("La hora de salida debe ser mayor a la de entrada.")
                else:
                    emp_id = emp_map[tecnico]
                    ok, msg = guardar_registro({
                        "empleado_id": emp_id,
                        "nombre": tecnico,
                        "fecha": fecha.strftime("%Y-%m-%d"),
                        "hora_entrada": entrada.strip(),
                        "hora_salida": salida.strip(),
                        "horas_trabajadas": round(trabajado, 4),
                        "diferencia": round(diferencia, 4),
                        "inicio_ruta": inicio_ruta,
                        "fin_ruta": fin_ruta,
                    })
                    if ok:
                        bal = decimal_a_hhmm(diferencia)
                        st.success(f"✅ Registro guardado — Trabajado: {decimal_a_hhmm(trabajado)} | Balance: {bal}")
                    else:
                        st.error(msg)
            except ValueError:
                st.error("Formato de hora inválido. Usá HH:MM (ej: 08:00).")

    st.markdown("---")
    st.caption("💡 Si ya existe un registro para esa fecha, editalo desde Historial.")


# ══════════════════════════════════════════════════════════════════
# PÁGINA: HISTORIAL
# ══════════════════════════════════════════════════════════════════
def pagina_historial():
    st.markdown("### 📋 Historial de registros")

    registros = cargar_registros()
    empleados = cargar_empleados(solo_activos=False)
    nombres_todos = ["Todos"] + [e["nombre"] for e in empleados]

    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_emp = st.selectbox("Técnico", nombres_todos)
    with col2:
        filtro_desde = st.date_input("Desde", value=date.today().replace(day=1))
    with col3:
        filtro_hasta = st.date_input("Hasta", value=date.today())

    filtrados = registros
    if filtro_emp != "Todos":
        filtrados = [r for r in filtrados if r["nombre"] == filtro_emp]
    filtrados = [r for r in filtrados if filtro_desde.strftime("%Y-%m-%d") <= r["fecha"] <= filtro_hasta.strftime("%Y-%m-%d")]
    filtrados = sorted(filtrados, key=lambda x: x["fecha"], reverse=True)

    if not filtrados:
        st.info("No hay registros con ese filtro.")
        return

    # Tabla
    df = pd.DataFrame([{
        "ID": r["id"],
        "Técnico": r["nombre"],
        "Fecha": r["fecha"],
        "Entrada": r["hora_entrada"],
        "Salida": r["hora_salida"],
        "Inicio Ruta": r["inicio_ruta"],
        "Fin Ruta": r.get("fin_ruta", ""),
        "Trabajado": decimal_a_hhmm(r["horas_trabajadas"]),
        "Balance": decimal_a_hhmm(r["diferencia"]),
    } for r in filtrados])

    st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)

    # Editar / Eliminar
    st.markdown("---")
    st.markdown("**Editar o eliminar un registro**")

    opciones = [f"{r['fecha']} | {r['nombre']} | {r['hora_entrada']}→{r['hora_salida']}" for r in filtrados]
    sel = st.selectbox("Seleccioná un registro", opciones)
    idx_sel = opciones.index(sel)
    reg_sel = filtrados[idx_sel]

    col_e, col_d = st.columns(2)
    with col_e:
        if st.button("✏️ Editar seleccionado", use_container_width=True):
            st.session_state["editar_reg"] = reg_sel.copy()
    with col_d:
        if st.button("🗑️ Eliminar seleccionado", use_container_width=True, type="secondary"):
            eliminar_registro(reg_sel["id"])
            st.success("Registro eliminado.")
            st.rerun()

    # Formulario de edición
    if "editar_reg" in st.session_state:
        g = st.session_state["editar_reg"]
        st.markdown("---")
        st.markdown(f"**✏️ Editando — {g['nombre']} | {g['fecha']}**")

        with st.form("form_editar_reg"):
            c1, c2 = st.columns(2)
            with c1:
                e_fecha = st.date_input("Fecha", value=datetime.strptime(g["fecha"], "%Y-%m-%d").date())
                e_entrada = st.text_input("Entrada (HH:MM)", value=g["hora_entrada"])
                e_inicio = st.text_input("Inicio de ruta", value=g.get("inicio_ruta", ""))
            with c2:
                e_salida = st.text_input("Salida (HH:MM)", value=g["hora_salida"])
                e_fin = st.text_input("Fin de ruta", value=g.get("fin_ruta", ""))

            guardar_btn = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
            if guardar_btn:
                try:
                    trabajado, diferencia = calcular_horas(e_entrada, e_salida)
                    if trabajado is None:
                        st.error("La hora de salida debe ser mayor a la de entrada.")
                    else:
                        ok = actualizar_registro(g["id"], {
                            "empleado_id": g["empleado_id"],
                            "nombre": g["nombre"],
                            "fecha": e_fecha.strftime("%Y-%m-%d"),
                            "hora_entrada": e_entrada.strip(),
                            "hora_salida": e_salida.strip(),
                            "horas_trabajadas": round(trabajado, 4),
                            "diferencia": round(diferencia, 4),
                            "inicio_ruta": e_inicio,
                            "fin_ruta": e_fin,
                        })
                        if ok:
                            del st.session_state["editar_reg"]
                            st.success("Registro actualizado.")
                            st.rerun()
                        else:
                            st.error("No se pudo actualizar el registro.")
                except ValueError:
                    st.error("Formato de hora inválido.")


# ══════════════════════════════════════════════════════════════════
# PÁGINA: RESUMEN + EXCEL
# ══════════════════════════════════════════════════════════════════
def pagina_resumen():
    st.markdown("### 📊 Resumen mensual + Excel")

    col1, col2 = st.columns(2)
    with col1:
        mes_sel = st.selectbox("Mes", MESES, index=date.today().month - 1)
    with col2:
        anio_sel = st.selectbox("Año", [2024, 2025, 2026, 2027], index=2)

    mes_num = str(MESES.index(mes_sel) + 1).zfill(2)
    anio_str = str(anio_sel)

    registros = cargar_registros()
    filtrados = [r for r in registros if r["fecha"].startswith(f"{anio_str}-{mes_num}")]

    if not filtrados:
        st.info(f"No hay registros para {mes_sel} {anio_sel}.")
        return

    # Resumen por técnico
    resumen = {}
    for r in filtrados:
        n = r["nombre"]
        if n not in resumen:
            resumen[n] = {"dias": 0, "trabajado": 0.0, "balance": 0.0}
        resumen[n]["dias"] += 1
        resumen[n]["trabajado"] += r["horas_trabajadas"]
        resumen[n]["balance"] += r["diferencia"]

    df_res = pd.DataFrame([{
        "Técnico": n,
        "Días": v["dias"],
        "Trabajado": decimal_a_hhmm(v["trabajado"]),
        "Esperado": decimal_a_hhmm(v["dias"] * JORNADA_BASE),
        "Balance": decimal_a_hhmm(v["balance"]),
    } for n, v in sorted(resumen.items())])

    st.dataframe(df_res, use_container_width=True, hide_index=True)

    # Totales
    st.markdown("---")
    total_dias = sum(v["dias"] for v in resumen.values())
    total_trab = sum(v["trabajado"] for v in resumen.values())
    total_bal = sum(v["balance"] for v in resumen.values())

    m1, m2, m3 = st.columns(3)
    m1.metric("📅 Total jornadas", total_dias)
    m2.metric("⏱️ Total trabajado", decimal_a_hhmm(total_trab))
    m3.metric("⚖️ Balance global", decimal_a_hhmm(total_bal))

    # Export Excel
    st.markdown("---")
    if st.button("📥 Exportar Excel", use_container_width=True):
        wb = Workbook()

        # Hoja Resumen
        ws1 = wb.active
        ws1.title = "Resumen"
        azul = PatternFill("solid", fgColor="1E3A8A")
        headers1 = ["Técnico", "Días", "Trabajado", "Esperado", "Balance"]
        ws1.append(headers1)
        for c in ws1[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = azul
            c.alignment = Alignment(horizontal="center")
        for _, row_data in df_res.iterrows():
            ws1.append(list(row_data))
        for row in ws1.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")

        # Hoja Detalle
        ws2 = wb.create_sheet("Detalle")
        headers2 = ["Técnico", "Fecha", "Entrada", "Salida", "Inicio Ruta", "Fin Ruta", "Trabajado", "Balance"]
        ws2.append(headers2)
        for c in ws2[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = azul
            c.alignment = Alignment(horizontal="center")
        for r in sorted(filtrados, key=lambda x: (x["nombre"], x["fecha"])):
            ws2.append([
                r["nombre"], r["fecha"], r["hora_entrada"], r["hora_salida"],
                r.get("inicio_ruta", ""), r.get("fin_ruta", ""),
                decimal_a_hhmm(r["horas_trabajadas"]),
                decimal_a_hhmm(r["diferencia"]),
            ])
        for row in ws2.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")

        # Autosize
        for sheet in (ws1, ws2):
            for col in sheet.columns:
                max_len = max((len(str(c.value or "")) for c in col), default=10)
                sheet.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        st.download_button(
            label=f"⬇️ Descargar Resumen_{mes_num}_{anio_str}.xlsx",
            data=buf,
            file_name=f"Resumen_{mes_num}_{anio_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════
# PÁGINA: ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════════
def pagina_estadisticas():
    st.markdown("### 📈 Estadísticas")

    registros = cargar_registros()
    if not registros:
        st.info("No hay registros para mostrar estadísticas.")
        return

    empleados = cargar_empleados(solo_activos=False)
    nombres_todos = ["Todos"] + [e["nombre"] for e in empleados]

    col1, col2 = st.columns(2)
    with col1:
        filtro_emp = st.selectbox("Técnico", nombres_todos, key="est_emp")
    with col2:
        anio_sel = st.selectbox("Año", [2024, 2025, 2026, 2027], index=2, key="est_anio")

    filtrados = [r for r in registros if r["fecha"].startswith(str(anio_sel))]
    if filtro_emp != "Todos":
        filtrados = [r for r in filtrados if r["nombre"] == filtro_emp]

    if not filtrados:
        st.info("No hay datos con ese filtro.")
        return

    # Métricas globales
    total_dias = len(filtrados)
    total_horas = sum(r["horas_trabajadas"] for r in filtrados)
    total_balance = sum(r["diferencia"] for r in filtrados)
    promedio_diario = total_horas / total_dias if total_dias else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📅 Jornadas registradas", total_dias)
    m2.metric("⏱️ Total horas", decimal_a_hhmm(total_horas))
    m3.metric("📊 Promedio diario", decimal_a_hhmm(promedio_diario))
    m4.metric("⚖️ Balance acumulado", decimal_a_hhmm(total_balance))

    st.markdown("---")

    # Por mes
    st.markdown("#### Horas por mes")
    por_mes = {}
    for r in filtrados:
        mes_num = int(r["fecha"][5:7])
        nombre_mes = MESES[mes_num - 1]
        if nombre_mes not in por_mes:
            por_mes[nombre_mes] = {"trabajado": 0.0, "balance": 0.0, "dias": 0}
        por_mes[nombre_mes]["trabajado"] += r["horas_trabajadas"]
        por_mes[nombre_mes]["balance"] += r["diferencia"]
        por_mes[nombre_mes]["dias"] += 1

    # Ordenar por mes
    por_mes_ord = {MESES[i]: por_mes[MESES[i]] for i in range(12) if MESES[i] in por_mes}

    df_mes = pd.DataFrame([{
        "Mes": k,
        "Días": v["dias"],
        "Horas trabajadas": round(v["trabajado"], 2),
        "Balance (h)": round(v["balance"], 2),
    } for k, v in por_mes_ord.items()])

    st.bar_chart(df_mes.set_index("Mes")[["Horas trabajadas"]])
    st.dataframe(df_mes, use_container_width=True, hide_index=True)

    # Por técnico (solo si filtro = Todos)
    if filtro_emp == "Todos":
        st.markdown("---")
        st.markdown("#### Ranking de horas por técnico")
        por_tec = {}
        for r in filtrados:
            n = r["nombre"]
            if n not in por_tec:
                por_tec[n] = {"trabajado": 0.0, "dias": 0, "balance": 0.0}
            por_tec[n]["trabajado"] += r["horas_trabajadas"]
            por_tec[n]["dias"] += 1
            por_tec[n]["balance"] += r["diferencia"]

        df_tec = pd.DataFrame([{
            "Técnico": n,
            "Jornadas": v["dias"],
            "Total horas": round(v["trabajado"], 2),
            "Balance (h)": round(v["balance"], 2),
        } for n, v in sorted(por_tec.items(), key=lambda x: -x[1]["trabajado"])])

        st.bar_chart(df_tec.set_index("Técnico")[["Total horas"]])
        st.dataframe(df_tec, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
# PÁGINA: TÉCNICOS
# ══════════════════════════════════════════════════════════════════
def pagina_tecnicos():
    st.markdown("### 👷 Técnicos")

    tab1, tab2 = st.tabs(["👥 Ver / Editar", "➕ Nuevo técnico"])

    with tab1:
        empleados = cargar_empleados(solo_activos=False)
        if not empleados:
            st.info("No hay técnicos cargados todavía.")
        else:
            for emp in empleados:
                estado = "🟢 Activo" if emp["activo"] else "🔴 Inactivo"
                with st.expander(f"**{emp['nombre']}** — {estado}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"📞 **Tel:** {emp['telefono'] or '—'}")
                        st.markdown(f"🪪 **DNI:** {emp['dni'] or '—'}")
                        st.markdown(f"📍 **Zona:** {emp['zona'] or '—'}")
                    with col2:
                        st.markdown(f"🚗 **Vehículo:** {emp['vehiculo'] or '—'}")
                        st.markdown(f"🔖 **Patente:** {emp['patente'] or '—'}")
                    if emp['observaciones']:
                        st.markdown(f"📝 **Obs:** {emp['observaciones']}")

                    if st.button(f"✏️ Editar {emp['nombre']}", key=f"edit_{emp['id']}"):
                        st.session_state["editar_emp"] = emp.copy()

        # Formulario de edición
        if "editar_emp" in st.session_state:
            e = st.session_state["editar_emp"]
            st.markdown("---")
            st.markdown(f"**✏️ Editando — {e['nombre']}**")
            with st.form("form_edit_emp"):
                c1, c2 = st.columns(2)
                with c1:
                    e_nombre = st.text_input("Nombre", value=e["nombre"])
                    e_tel = st.text_input("Teléfono", value=e.get("telefono", ""))
                    e_dni = st.text_input("DNI", value=e.get("dni", ""))
                    e_zona = st.text_input("Zona", value=e.get("zona", ""))
                with c2:
                    e_veh = st.text_input("Vehículo", value=e.get("vehiculo", ""))
                    e_pat = st.text_input("Patente", value=e.get("patente", ""))
                    e_activo = st.checkbox("Activo", value=e.get("activo", True))
                e_obs = st.text_area("Observaciones", value=e.get("observaciones", ""))

                if st.form_submit_button("💾 Guardar cambios", use_container_width=True):
                    if not e_nombre:
                        st.error("El nombre no puede estar vacío.")
                    else:
                        actualizar_empleado(e["id"], {
                            "nombre": e_nombre,
                            "activo": e_activo,
                            "telefono": e_tel,
                            "dni": e_dni,
                            "zona": e_zona,
                            "vehiculo": e_veh,
                            "patente": e_pat,
                            "observaciones": e_obs,
                        })
                        del st.session_state["editar_emp"]
                        st.success("Técnico actualizado.")
                        st.rerun()

    with tab2:
        st.markdown("#### Nuevo técnico")
        with st.form("form_nuevo_emp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n_nombre = st.text_input("Nombre *", placeholder="Maxi")
                n_tel = st.text_input("Teléfono", placeholder="11 1234-5678")
                n_dni = st.text_input("DNI", placeholder="12345678")
                n_zona = st.text_input("Zona", placeholder="CABA / Zona Oeste")
            with c2:
                n_veh = st.text_input("Vehículo", placeholder="Partner / Moto")
                n_pat = st.text_input("Patente", placeholder="AB123CD")
                n_activo = st.checkbox("Activo", value=True)
            n_obs = st.text_area("Observaciones")

            if st.form_submit_button("💾 Guardar técnico", use_container_width=True):
                if not n_nombre:
                    st.error("El nombre es obligatorio.")
                else:
                    guardar_empleado_nuevo({
                        "nombre": n_nombre,
                        "activo": n_activo,
                        "telefono": n_tel,
                        "dni": n_dni,
                        "zona": n_zona,
                        "vehiculo": n_veh,
                        "patente": n_pat,
                        "observaciones": n_obs,
                    })
                    st.success(f"✅ Técnico '{n_nombre}' agregado.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "registro"

    if not st.session_state["usuario"]:
        pagina_login()
        return

    # Inicializar hojas si no existen
    _init_empleados_ws()
    _init_registros_ws()

    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='padding: 20px 0 16px'>
            <div style='font-size:24px; font-weight:700; color:#111827'>🕐 Horarios</div>
            <div style='font-size:12px; color:#6b7280; margin-top:4px'>Usuario: {st.session_state['usuario']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        paginas = {
            "registro": "➕  Registro",
            "historial": "📋  Historial",
            "resumen": "📊  Resumen + Excel",
            "estadisticas": "📈  Estadísticas",
            "tecnicos": "👷  Técnicos",
        }

        for key, label in paginas.items():
            activo = st.session_state["pagina"] == key
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                        type="primary" if activo else "secondary"):
                st.session_state["pagina"] = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state["usuario"] = None
            st.session_state["pagina"] = "registro"
            st.rerun()

    # Contenido
    pagina = st.session_state["pagina"]
    if pagina == "registro":
        pagina_registro()
    elif pagina == "historial":
        pagina_historial()
    elif pagina == "resumen":
        pagina_resumen()
    elif pagina == "estadisticas":
        pagina_estadisticas()
    elif pagina == "tecnicos":
        pagina_tecnicos()


if __name__ == "__main__":
    main()
