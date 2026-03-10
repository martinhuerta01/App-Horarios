import streamlit as st
from db.sheets import get_ws, clear_cache


@st.cache_data(ttl=300)
def cargar_usuarios() -> dict:
    ws = get_ws("usuarios")
    vals = ws.get_all_values()
    if not vals:
        default = {"Alejo": "1234", "Martin": "1234"}
        ws.append_rows([[u, p] for u, p in default.items()])
        return default
    return {r[0]: r[1] for r in vals if len(r) >= 2 and r[0]}


def validar_usuario(usuario: str, password: str) -> bool:
    return cargar_usuarios().get(usuario) == password
