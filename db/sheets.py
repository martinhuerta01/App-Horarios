"""
Conexión a Google Sheets.
- get_sheet()  → objeto Spreadsheet (cacheado indefinidamente por sesión)
- get_ws(name) → worksheet por nombre, creándola si no existe
- clear_cache() → invalida todos los datos cacheados (llamar después de writes)
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from config import SCOPES


@st.cache_resource
def get_sheet():
    """Abre el Spreadsheet una sola vez por sesión del servidor."""
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(dict(creds_dict), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheet_id"])


def get_ws(name: str):
    """Devuelve un worksheet, lo crea si no existe."""
    sh = get_sheet()
    try:
        return sh.worksheet(name)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=name, rows=2000, cols=20)


def clear_cache():
    """Invalida todos los datos cacheados (llamar tras cualquier write)."""
    st.cache_data.clear()
