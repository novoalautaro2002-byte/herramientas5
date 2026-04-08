"""
app.py — Portfolio Investment
Página principal: Resumen de mercado.
Para ejecutar: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import apply_style, page_header, fetch_bonds, fetch_notes, fetch_dolar, fmt_pct, fmt_ars, fmt_usd

st.set_page_config(
    page_title="Portfolio Investment",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Portfolio Investment — Sistema de Cálculo Financiero\nBYMA · MERVAL · MCE"}
)
apply_style()

# ─── Sidebar branding ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 12px 0">
        <div style="font-size:1.1rem;font-weight:800;color:#f0f4ff;letter-spacing:-.01em">📊 Portfolio Investment</div>
        <div style="font-size:0.7rem;color:#7aa3f0;text-transform:uppercase;letter-spacing:.1em">Sistema de Cálculo Financiero</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}  ·  BYMA · MERVAL · MCE")

# ─── Page content ─────────────────────────────────────────────────────────────
page_header("Resumen de Mercado", subtitle="Portfolio Investment · BYMA 2026", icon="◉")

col_ref, _ = st.columns([1, 3])
with col_ref:
    if st.button("🔄 Actualizar precios", use_container_width=True):
        fetch_bonds.clear()
        fetch_notes.clear()
        fetch_dolar.clear()
        st.rerun()

# ─── Fetch data ───────────────────────────────────────────────────────────────
with st.spinner("Cargando datos de mercado…"):
    bond_prices = fetch_bonds()
    note_prices = fetch_notes()
    dolar_data  = fetch_dolar()

# ─── FX Row ───────────────────────────────────────────────────────────────────
st.markdown("#### 💵 Tipos de Cambio")
fx_cols = st.columns(5)
fx_labels = [
    ("oficial", "Dólar Oficial"),
    ("mep",     "Dólar MEP"),
    ("contadoconliqui", "Dólar CCL"),
    ("blue",    "Dólar Blue"),
    ("cripto",  "Dólar Cripto"),
]
for col, (key, label) in zip(fx_cols, fx_labels):
    d = dolar_data.get(key, {})
    venta = d.get("venta")
    compra = d.get("compra")
    with col:
        if venta:
            st.metric(label, f"${venta:,.2f}", f"Cpa ${compra:,.2f}" if compra else None)
        else:
            st.metric(label, "—")

st.divider()

# ─── Bonares / Globales ───────────────────────────────────────────────────────
BONARES  = ["AL29","AL30","AL35","AL38","AL41"]
GLOBALES = ["GD29","GD30","GD35","GD38","GD41","GD46"]

def make_bond_df(tickers, prices):
    rows = []
    for t in tickers:
        p = prices.get(t)
        rows.append({
            "Ticker": t,
            "Último (USD)": f"{p:.4f}" if p else "—",
        })
    return pd.DataFrame(rows)

col_bon, col_glo = st.columns(2)

with col_bon:
    st.markdown("#### 🇦🇷 Bonares (Ley Argentina)")
    df_b = make_bond_df(BONARES, bond_prices)
    st.dataframe(df_b, use_container_width=True, hide_index=True,
                 column_config={"Último (USD)": st.column_config.TextColumn(width="medium")})

with col_glo:
    st.markdown("#### 🌐 Globales (Ley NY)")
    df_g = make_bond_df(GLOBALES, bond_prices)
    st.dataframe(df_g, use_container_width=True, hide_index=True)

st.divider()

# ─── LECAP / BONCAP ───────────────────────────────────────────────────────────
LECAPS = [k for k in note_prices if k.startswith("S") or k.startswith("T")]

if LECAPS:
    st.markdown("#### ◆ LECAP / BONCAP (Pesos)")
    rows = []
    for t in sorted(LECAPS)[:20]:
        p = note_prices[t]
        rows.append({"Ticker": t, "Último ($)": f"${p:,.4f}"})
    df_lec = pd.DataFrame(rows)
    st.dataframe(df_lec, use_container_width=True, hide_index=True)
else:
    st.info("No se encontraron LECAP/BONCAP en el feed de data912.com")

st.divider()

# ─── Pares MEP implícitos ─────────────────────────────────────────────────────
st.markdown("#### ⚡ TC Implícito MEP / CCL (sin comisiones)")

mep_pairs = [
    ("AL30",  "AL30D", "MEP via AL30"),
    ("GD30",  "GD30D", "MEP via GD30"),
    ("AL30",  "AL30C", "CCL via AL30"),
    ("GD30",  "GD30C", "CCL via GD30"),
]
tc_cols = st.columns(4)
for col, (ars_t, usd_t, label) in zip(tc_cols, mep_pairs):
    p_ars = bond_prices.get(ars_t)
    p_usd = bond_prices.get(usd_t)
    with col:
        if p_ars and p_usd and p_usd > 0:
            tc = p_ars / p_usd
            st.metric(label, f"${tc:,.2f}")
        else:
            st.metric(label, "—", help=f"Necesita {ars_t} y {usd_t} en feed")

st.caption("ℹ️ TC implícito = precio ARS / precio USD del bono. No incluye comisiones ni DDMM.")
