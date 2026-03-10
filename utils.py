from datetime import datetime
from config import JORNADA_BASE


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
    try:
        h_ent = parse_hora(entrada)
        h_sal = parse_hora(salida)
    except ValueError:
        return None, None
    if h_sal <= h_ent:
        return None, None
    diff = h_sal - h_ent
    trabajado = diff.total_seconds() / 3600
    return trabajado, trabajado - JORNADA_BASE
