"""
utils.py — Portfolio Investment
Funciones compartidas: APIs, math financiero, estilos.
"""
import streamlit as st
import requests
import numpy as np
from datetime import date

# ─── Estilos Bloomberg-style ──────────────────────────────────────────────────

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

.stApp { background-color: #0d1b2e !important; color: #f0f4ff; }
section[data-testid="stSidebar"] { background-color: #122540 !important; border-right: 1px solid #2a4a7a !important; }
section[data-testid="stSidebar"] * { color: #d0ddf5 !important; }
.main .block-container { padding-top: 1.2rem; max-width: 1400px; }

/* Métricas */
div[data-testid="stMetricValue"] > div {
    color: #e8f43a !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] > div {
    color: #7a99c4 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="stMetricDelta"] svg { display: none; }

/* Inputs */
.stNumberInput input, .stTextInput input {
    background-color: #0d1b2e !important;
    color: #e8f43a !important;
    border: 1px solid #2a4a7a !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.stNumberInput input:focus, .stTextInput input:focus {
    border-color: #3a6fd8 !important;
    box-shadow: 0 0 0 3px rgba(58,111,216,0.2) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #122540 !important;
    color: #f0f4ff !important;
    border: 1px solid #2a4a7a !important;
    border-radius: 4px !important;
}

/* Botones */
.stButton > button {
    background-color: #3a6fd8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background-color: #5b8def !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background-color: #122540; border-bottom: 2px solid #2a4a7a; gap: 0; }
.stTabs [data-baseweb="tab"] {
    color: #7a99c4 !important;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 6px 18px;
    background: transparent !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #f0f4ff !important;
    border-bottom: 2px solid #3a6fd8 !important;
    background: rgba(58,111,216,0.12) !important;
}

/* Tablas */
.stDataFrame { border: 1px solid #2a4a7a !important; border-radius: 6px; }
thead tr th { background-color: #1a3358 !important; color: #7aa3f0 !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
tbody tr td { background-color: #122540 !important; color: #f0f4ff !important; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
tbody tr:hover td { background-color: #1e3a62 !important; }

/* Headings */
h1, h2, h3 { color: #7aa3f0 !important; font-family: 'Inter', sans-serif !important; }
h1 { font-size: 1.4rem !important; letter-spacing: -0.02em; }
h2 { font-size: 1.1rem !important; }
h3 { font-size: 0.95rem !important; }

/* Divider */
hr { border-color: #2a4a7a !important; margin: 0.8rem 0; }

/* Warnings / Info */
.stAlert { background-color: #172d4d !important; border-left: 3px solid #f0b429 !important; color: #d0ddf5 !important; }

/* Slider */
.stSlider > div > div > div { background: #3a6fd8 !important; }

/* Radio */
.stRadio > div { gap: 4px; }
.stRadio [data-testid="stMarkdownContainer"] p { color: #d0ddf5 !important; font-size: 0.8rem; }
</style>
"""

def apply_style():
    st.markdown(STYLE, unsafe_allow_html=True)

# ─── Page header ─────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(f"""
    <div style="background:linear-gradient(90deg,#172d4d,#122540);border-bottom:1px solid #2a4a7a;
                padding:10px 0 10px 0;margin-bottom:16px">
        <div style="font-size:10px;color:#7a99c4;text-transform:uppercase;letter-spacing:.12em;font-family:monospace">{subtitle}</div>
        <div style="font-size:1.3rem;font-weight:800;color:#f0f4ff;letter-spacing:-.01em">{icon} {title}</div>
    </div>
    """, unsafe_allow_html=True)

# ─── API fetchers ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=25)
def fetch_bonds():
    """Precios de bonos soberanos desde data912.com"""
    try:
        r = requests.get("https://data912.com/live/arg_bonds", timeout=7)
        r.raise_for_status()
        return {d['s']: float(d['c']) for d in r.json() if d.get('c') and float(d['c']) > 0}
    except Exception as e:
        return {}

@st.cache_data(ttl=25)
def fetch_notes():
    """LECAP, BONCAP, otros instrumentos en pesos"""
    try:
        r = requests.get("https://data912.com/live/arg_notes", timeout=7)
        r.raise_for_status()
        return {d['s']: float(d['c']) for d in r.json() if d.get('c') and float(d['c']) > 0}
    except Exception as e:
        return {}

@st.cache_data(ttl=30)
def fetch_dolar():
    """FX desde dolarapi.com"""
    try:
        r = requests.get("https://dolarapi.com/v1/dolares", timeout=7)
        r.raise_for_status()
        return {d['casa'].lower(): d for d in r.json()}
    except:
        return {}

@st.cache_data(ttl=3600)
def fetch_cer() -> list:
    """Índice CER desde ArgentinaDatos"""
    try:
        r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/cer", timeout=10)
        r.raise_for_status()
        return r.json()  # [{"fecha": "YYYY-MM-DD", "valor": float}, ...]
    except:
        return []

def get_cer_value(fecha: date, cer_data: list) -> float | None:
    """Busca el valor del CER para una fecha dada (o la más cercana anterior)."""
    if not cer_data:
        return None
    str_fecha = fecha.isoformat()
    best = None
    for entry in cer_data:
        if entry["fecha"] <= str_fecha:
            best = float(entry["valor"])
        else:
            break
    return best

# ─── Math financiero ──────────────────────────────────────────────────────────

def newton_raphson_tir(precio_sucio: float, cashflows: list[tuple], guess: float = 0.08) -> tuple:
    """
    TIR para bonos USD con capitalización semestral.
    
    Parámetros:
        precio_sucio: precio dirty (cotización + interés corrido), por ej. 55.40 sobre 100 VN
        cashflows: [(date, monto), ...] — flujos futuros por cada 100 VN
        guess: tasa inicial (TNA decimal)
    
    Retorna:
        (tna, tea, duracion_modificada)  o  (None, None, None) si no converge
    """
    hoy = date.today()
    flows = [(d, m) for d, m in cashflows if d > hoy and m > 0]
    if not flows:
        return None, None, None

    def f(r):
        return sum(m / (1 + r/2)**(2*(d - hoy).days/365.25) for d, m in flows) - precio_sucio

    def df(r):
        return sum(
            -(d - hoy).days/365.25 * m / (1 + r/2)**(2*(d - hoy).days/365.25 + 1)
            for d, m in flows
        )

    r = guess
    for _ in range(400):
        fv, dfv = f(r), df(r)
        if abs(dfv) < 1e-15:
            break
        r_new = r - fv / dfv
        r_new = max(min(r_new, 5.0), -0.99)
        if abs(r_new - r) < 1e-10:
            r = r_new
            break
        r = r_new

    if not (-0.5 < r < 5):
        return None, None, None

    tna = r
    tea = (1 + r/2)**2 - 1

    # Duración de Macaulay y Modificada
    mac_dur = sum(
        (d - hoy).days/365.25 * m / (1 + r/2)**(2*(d - hoy).days/365.25)
        for d, m in flows
    ) / precio_sucio
    mod_dur = mac_dur / (1 + r/2)

    return tna, tea, mod_dur


def newton_raphson_tir_pesos(precio: float, cashflows: list[tuple], act360: bool = True) -> float | None:
    """
    TIR para instrumentos en pesos (LECAPs, CER, etc).
    Convención Act/360 (act360=True) o Act/365 (act360=False).
    Capitalización compuesta continua (un único período hasta vencimiento para ZC).
    Retorna TNA decimal o None.
    """
    hoy = date.today()
    flows = [(d, m) for d, m in cashflows if d > hoy and m > 0]
    if not flows:
        return None

    base = 360 if act360 else 365

    def f(r):
        total = 0.0
        for d, m in flows:
            t = (d - hoy).days / base
            total += m / (1 + r * t)
        return total - precio

    def df_r(r):
        total = 0.0
        for d, m in flows:
            t = (d - hoy).days / base
            total -= t * m / (1 + r * t)**2
        return total

    r = 0.5
    for _ in range(300):
        fv, dfv = f(r), df_r(r)
        if abs(dfv) < 1e-15:
            break
        r_new = r - fv / dfv
        r_new = max(min(r_new, 50.0), -0.99)
        if abs(r_new - r) < 1e-10:
            r = r_new
            break
        r = r_new

    return r if -0.5 < r < 50 else None


# ─── Cashflows de bonos soberanos USD ────────────────────────────────────────
# Fuente: prospectos canje 2020 (Ministerio de Economía Argentina)
# ⚠️  Verificar siempre contra rendimientos.co ante cualquier discrepancia.

def _semiannual_dates(start: date, end: date) -> list[date]:
    """Genera fechas semi-anuales 9-Ene / 9-Jul desde start hasta end (inclusive)."""
    dates = []
    d = start
    while d <= end:
        dates.append(d)
        if d.month == 1:
            d = date(d.year, 7, 9)
        else:
            d = date(d.year + 1, 1, 9)
    return dates


def get_bond_cashflows(ticker: str) -> list[tuple]:
    """
    Flujos de fondos por cada $100 VN para bonos soberanos USD.
    Retorna [(date, monto), ...] ordenados por fecha.
    """
    t = ticker.upper().strip()

    # ── AL30 / GD30 (2030) ──────────────────────────────────────────────────
    # Emission: 4-Sep-2020 | Vencimiento: 9-Jul-2030
    # Cupón anual step-up sobre outstanding:
    #   Hasta Jul-2024: 0.50% | Desde Ene-2025: 3.875%
    # Amortización: 10 pagos del 10% c/u, semi-anual, Ene-2025 → Jul-2029
    # Último flujo principal: Jul-2030 (último 10% + cupón final sobre 10%)
    if t in ("AL30", "GD30"):
        dates = _semiannual_dates(date(2021, 1, 9), date(2030, 7, 9))
        flows = []
        outstanding = 100.0
        # Amortization payments start Jan-2025
        amort_start = date(2025, 1, 9)
        amort_per_period = 10.0  # 10% per period, 10 periods = 100%
        amort_count = 0

        for d in dates:
            # Coupon rate (semi-annual, on outstanding)
            if d < date(2025, 1, 9):
                semi_cpn_rate = 0.005 / 2   # 0.50% annual / 2
            else:
                semi_cpn_rate = 0.03875 / 2  # 3.875% annual / 2

            coupon = outstanding * semi_cpn_rate

            amort = 0.0
            if d >= amort_start and amort_count < 10:
                amort = amort_per_period
                amort_count += 1

            flows.append((d, round(coupon + amort, 6)))
            outstanding -= amort

        return [(d, m) for d, m in flows if m > 0.0001]

    # ── AL29 / GD29 (2029) ──────────────────────────────────────────────────
    # Emission: 4-Sep-2020 | Vencimiento: 9-Jul-2029
    # Cupón: 1.125% annual → 0.5625% por período
    # Amortización: bullet (100% al vencimiento)
    if t in ("AL29", "GD29"):
        dates = _semiannual_dates(date(2021, 1, 9), date(2029, 7, 9))
        flows = []
        for d in dates:
            cpn = 100.0 * (0.01125 / 2)
            amort = 100.0 if d == date(2029, 7, 9) else 0.0
            flows.append((d, round(cpn + amort, 6)))
        return flows

    # ── AL35 / GD35 (2035) ──────────────────────────────────────────────────
    # Cupón: 3.625% annual | Semi-annual Jan 9 / Jul 9
    # Amortización: 12 pagos iguales desde Jul-2029 a Ene-2035 (aprox 8.33% c/u)
    if t in ("AL35", "GD35"):
        dates = _semiannual_dates(date(2021, 1, 9), date(2035, 1, 9))
        flows = []
        outstanding = 100.0
        amort_start = date(2029, 7, 9)
        amort_per_period = round(100.0 / 12, 8)
        amort_count = 0

        for d in dates:
            cpn = outstanding * (0.03625 / 2)
            amort = 0.0
            if d >= amort_start and amort_count < 12:
                amort = amort_per_period
                amort_count += 1
            flows.append((d, round(cpn + amort, 6)))
            outstanding -= amort

        return [(d, m) for d, m in flows if m > 0.0001]

    # ── AL38 / GD38 (2038) ──────────────────────────────────────────────────
    # Cupón: 3.625% | Bullet 2038
    if t in ("AL38", "GD38"):
        dates = _semiannual_dates(date(2021, 1, 9), date(2038, 1, 9))
        flows = []
        for d in dates:
            cpn = 100.0 * (0.03625 / 2)
            amort = 100.0 if d == date(2038, 1, 9) else 0.0
            flows.append((d, round(cpn + amort, 6)))
        return flows

    # ── AL41 / GD41 (2041) ──────────────────────────────────────────────────
    # Cupón: 4.25% | Amortización semi-anual desde Jul-2034
    if t in ("AL41", "GD41"):
        dates = _semiannual_dates(date(2021, 1, 9), date(2041, 7, 9))
        flows = []
        outstanding = 100.0
        amort_start = date(2034, 7, 9)
        amort_per_period = 100.0 / 14  # 14 pagos semestrales
        amort_count = 0

        for d in dates:
            cpn = outstanding * (0.0425 / 2)
            amort = 0.0
            if d >= amort_start and amort_count < 14:
                amort = amort_per_period
                amort_count += 1
            flows.append((d, round(cpn + amort, 6)))
            outstanding -= amort

        return [(d, m) for d, m in flows if m > 0.0001]

    # ── GD46 (2046) ─────────────────────────────────────────────────────────
    # Solo Global (no tiene Bonar) | Cupón: 4.875% | Bullet
    if t == "GD46":
        dates = _semiannual_dates(date(2021, 1, 9), date(2046, 7, 9))
        flows = []
        for d in dates:
            cpn = 100.0 * (0.04875 / 2)
            amort = 100.0 if d == date(2046, 7, 9) else 0.0
            flows.append((d, round(cpn + amort, 6)))
        return flows

    return []  # Ticker no reconocido


# ─── Formateo ────────────────────────────────────────────────────────────────

def fmt_pct(v, d=2):
    return f"{v*100:.{d}f}%" if v is not None else "—"

def fmt_ars(v, d=2):
    return f"${v:,.{d}f}" if v is not None else "—"

def fmt_usd(v, d=4):
    return f"U$S {v:,.{d}f}" if v is not None else "—"

def colorcell(val, *, good_high=True):
    """Color verde/rojo para celdas de tabla."""
    if val is None:
        return ""
    color = "#22d68a" if (val >= 0) == good_high else "#ff4d6a"
    return f"color: {color}; font-family: 'JetBrains Mono', monospace; font-weight: 600"
