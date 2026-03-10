SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

JORNADA_BASE = 8.0

EQUIPOS = {
    "EQUIPO 1": "AB887CX",
    "EQUIPO 2": "AH453YE",
}

ESTADOS_SERVICIO = ["PENDIENTE", "CONFIRMADO", "REALIZADO", "SUSPENDIDO", "REPROGRAMADO"]

RESPONSABLES = ["EQUIPO 1", "EQUIPO 2", "VITACO", "ZARZA", "TALLER INTERNO", "OTRO"]

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

UBICACIONES_STOCK = ["Oficina", "Equipo 1", "Equipo 2", "Taller", "Mendoza", "Neuquén", "Córdoba"]

CATEGORIAS_STOCK = ["DISPOSITIVOS", "INSUMOS", "HERRAMIENTAS", "OTROS"]

TIPOS_SERVICIO = ["INSTALACION", "DESINSTALACION", "REVISION", "MANTENIMIENTO", "OTRO"]

# Módulos del sidebar — agregá acá para extender la app
MODULOS = [
    {
        "id": "horarios",
        "icon": "🕐",
        "label": "Horarios",
        "color": "#1e3a8a",
        "subs": [
            ("registro",     "➕  Registro"),
            ("historial",    "📋  Historial"),
            ("resumen",      "📊  Resumen + Excel"),
            ("estadisticas", "📈  Estadísticas"),
            ("tecnicos",     "👷  Técnicos"),
        ],
    },
    {
        "id": "servicios",
        "icon": "🔧",
        "label": "Servicios",
        "color": "#0f766e",
        "subs": [
            ("serv_cargar", "➕  Cargar servicio"),
            ("serv_lista",  "📋  Detalle / Lista"),
        ],
    },
    {
        "id": "stock",
        "icon": "📦",
        "label": "Stock",
        "color": "#b45309",
        "subs": [
            ("stock_actual",    "📊  Stock actual"),
            ("stock_entrada",   "📥  Entrada"),
            ("stock_salida",    "📤  Salida"),
            ("stock_productos", "⚙️  Productos"),
        ],
    },
    {
        "id": "reportes",
        "icon": "📑",
        "label": "Reportes",
        "color": "#be123c",
        "subs": [
            ("reporte_cruzado", "⚡  Horarios vs Servicios"),
        ],
    },
]
