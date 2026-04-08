"""
pages/9_⇄_Arbitraje.py
Arbitraje GD30/AL30: ratio, Bandas Bollinger, señal ¿Qué hacer?.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header, fetch_bonds

st.set_page_config(page_title="Arbitraje GD30/AL30", page_icon="⇄", layout="wide")
apply_style()
page_header("Arbitraje GD30 / AL30", subtitle="Ratio · Bandas Bollinger · Señal táctica", icon="⇄")

st.caption("Monitoreo del spread entre el Bono Global (GD30) y el Bonar (AL30). "
           "Ratio > 1 implica que GD30 cotiza con premio sobre AL30.")

# ─── Precios live ─────────────────────────────────────────────────────────────
col_ref, _ = st.columns([1, 4])
with col_ref:
    if st.button("🔄 Actualizar"):
        fetch_bonds.clear()
        st.rerun()

with st.spinner("Cargando precios…"):
    prices = fetch_bonds()

p_gd30 = prices.get("GD30")
p_al30 = prices.get("AL30")
p_gd30_ars = prices.get("GD30")  # precio en ARS si disponible
p_al30_ars = prices.get("AL30")

# ─── Ratio actual ─────────────────────────────────────────────────────────────
r1, r2, r3, r4 = st.columns(4)
with r1:
    st.metric("GD30 (USD)", f"U$S {p_gd30:.4f}" if p_gd30 else "—")
with r2:
    st.metric("AL30 (USD)", f"U$S {p_al30:.4f}" if p_al30 else "—")
with r3:
    if p_gd30 and p_al30 and p_al30 > 0:
        ratio_actual = p_gd30 / p_al30
        st.metric("Ratio GD30/AL30", f"{ratio_actual:.4f}")
    else:
        ratio_actual = None
        st.metric("Ratio GD30/AL30", "—")
with r4:
    if ratio_actual:
        spread_pct = (ratio_actual - 1) * 100
        st.metric("Spread (%)", f"{spread_pct:+.2f}%",
                  delta="GD30 con prima" if spread_pct > 0 else "AL30 con prima")

st.divider()

# ─── Historial simulado + Bollinger Bands ─────────────────────────────────────
st.markdown("#### 📈 Historial de Ratio y Bandas Bollinger")

with st.expander("⚙️ Configuración Bollinger Bands", expanded=False):
    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        bb_period = st.number_input("Período (N)", value=21, min_value=5, max_value=100, step=1)
    with bc2:
        bb_sigma = st.number_input("Desvíos (σ)", value=1.5, min_value=0.5, max_value=3.0, step=0.1)
    with bc3:
        n_puntos = st.number_input("Puntos históricos", value=60, min_value=20, max_value=252, step=10)

# Cargar historial desde session_state (simular persistencia)
if "ratio_history" not in st.session_state:
    st.session_state.ratio_history = []

# Si hay precio actual, agregarlo al historial
if ratio_actual:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Evitar duplicados por segundo
    if not st.session_state.ratio_history or st.session_state.ratio_history[-1]["ratio"] != ratio_actual:
        st.session_state.ratio_history.append({
            "fecha": now_str,
            "ratio": ratio_actual,
            "gd30": p_gd30,
            "al30": p_al30,
        })
        # Mantener solo últimos n_puntos × 2 puntos
        if len(st.session_state.ratio_history) > n_puntos * 3:
            st.session_state.ratio_history = st.session_state.ratio_history[-(n_puntos * 3):]

# ─── Upload de historial ──────────────────────────────────────────────────────
st.markdown("##### 📂 Cargar historial (CSV)")
st.caption("Podés subir un CSV con columnas: fecha, gd30, al30 (precios USD). El ratio se calcula automáticamente.")

uploaded = st.file_uploader("CSV con historial de precios", type=["csv"], label_visibility="collapsed")

hist_df = None
if uploaded:
    try:
        df_up = pd.read_csv(uploaded)
        if "gd30" in df_up.columns and "al30" in df_up.columns:
            df_up["ratio"] = df_up["gd30"] / df_up["al30"]
            hist_df = df_up
            st.success(f"✅ Cargado: {len(hist_df)} registros")
        else:
            st.error("El CSV necesita columnas 'gd30' y 'al30'")
    except Exception as e:
        st.error(f"Error leyendo CSV: {e}")

# Usar historial de session_state si no hay CSV
if hist_df is None and st.session_state.ratio_history:
    hist_df = pd.DataFrame(st.session_state.ratio_history)

if hist_df is not None and len(hist_df) >= 5:
    ratios = hist_df["ratio"].values
    n = len(ratios)

    # Bollinger Bands
    bb_mm = []
    bb_up = []
    bb_dn = []
    for i in range(n):
        if i < bb_period - 1:
            bb_mm.append(np.nan)
            bb_up.append(np.nan)
            bb_dn.append(np.nan)
        else:
            window = ratios[max(0, i - bb_period + 1):i + 1]
            mu = np.mean(window)
            sigma = np.std(window, ddof=1)
            bb_mm.append(mu)
            bb_up.append(mu + bb_sigma * sigma)
            bb_dn.append(mu - bb_sigma * sigma)

    # MM9 rápida
    mm9 = pd.Series(ratios).rolling(9).mean().values

    # Fechas
    fechas = hist_df.get("fecha", pd.RangeIndex(n)).values if "fecha" in hist_df.columns else list(range(n))

    # ─── Gráfico ─────────────────────────────────────────────────────────────
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(fechas), y=list(bb_up),
        name=f"BB+{bb_sigma}σ", line=dict(color="#ff4d6a", dash="dot", width=1),
        fill=None
    ))
    fig.add_trace(go.Scatter(
        x=list(fechas), y=list(bb_dn),
        name=f"BB-{bb_sigma}σ", line=dict(color="#22d68a", dash="dot", width=1),
        fill="tonexty", fillcolor="rgba(58,111,216,0.07)"
    ))
    fig.add_trace(go.Scatter(
        x=list(fechas), y=list(bb_mm),
        name=f"MM{bb_period}", line=dict(color="#f0b429", width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=list(fechas), y=list(mm9),
        name="MM9", line=dict(color="#22d4f0", width=1, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=list(fechas), y=list(ratios),
        name="Ratio GD30/AL30", line=dict(color="#5b8def", width=2),
        mode="lines+markers", marker=dict(size=3)
    ))

    fig.update_layout(
        title=f"Ratio GD30/AL30 con Bandas Bollinger ({bb_period} períodos, {bb_sigma}σ)",
        paper_bgcolor="#0d1b2e",
        plot_bgcolor="#122540",
        font=dict(color="#f0f4ff", family="Inter"),
        legend=dict(bgcolor="#1a3358", bordercolor="#2a4a7a", orientation="h", y=-0.2),
        xaxis=dict(gridcolor="#2a4a7a"),
        yaxis=dict(gridcolor="#2a4a7a", title="Ratio"),
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── Señal táctica ────────────────────────────────────────────────────────
    st.markdown("#### ⚡ Señal táctica — ¿Qué hacer?")

    if not np.isnan(bb_mm[-1]) and not np.isnan(bb_up[-1]):
        ratio_now = ratios[-1]
        mm21_now  = bb_mm[-1]
        band_up   = bb_up[-1]
        band_dn   = bb_dn[-1]

        if ratio_now > band_up:
            señal = "🟥 VENDER GD30 / COMPRAR AL30"
            detalle = f"Ratio ({ratio_now:.4f}) por encima de BB+ ({band_up:.4f}). GD30 sobrevaluado relativo."
            color = "#ff4d6a"
        elif ratio_now < band_dn:
            señal = "🟩 COMPRAR GD30 / VENDER AL30"
            detalle = f"Ratio ({ratio_now:.4f}) por debajo de BB- ({band_dn:.4f}). AL30 sobrevaluado relativo."
            color = "#22d68a"
        elif ratio_now > mm21_now:
            señal = "🟡 MANTENER — tendencia GD30 sobre MM"
            detalle = f"Ratio ({ratio_now:.4f}) por encima de MM{bb_period} ({mm21_now:.4f}). Sin señal clara."
            color = "#f0b429"
        else:
            señal = "🟡 MANTENER — tendencia neutral"
            detalle = f"Ratio ({ratio_now:.4f}) bajo la MM{bb_period} ({mm21_now:.4f}). Sin señal clara."
            color = "#f0b429"

        st.markdown(f"""
        <div style="background:#1a3358;border:2px solid {color};border-radius:8px;padding:16px 20px">
            <div style="font-size:1.1rem;font-weight:700;color:{color}">{señal}</div>
            <div style="color:#d0ddf5;font-size:0.85rem;margin-top:6px">{detalle}</div>
            <div style="margin-top:10px;display:flex;gap:20px">
                <span style="color:#7a99c4;font-size:0.75rem">Ratio actual: <strong style="color:#e8f43a">{ratio_now:.4f}</strong></span>
                <span style="color:#7a99c4;font-size:0.75rem">MM{bb_period}: <strong style="color:#f0b429">{mm21_now:.4f}</strong></span>
                <span style="color:#7a99c4;font-size:0.75rem">BB+: <strong style="color:#ff4d6a">{band_up:.4f}</strong></span>
                <span style="color:#7a99c4;font-size:0.75rem">BB-: <strong style="color:#22d68a">{band_dn:.4f}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    if ratio_actual:
        st.info(f"📊 Ratio actual: **{ratio_actual:.4f}**. "
                f"Se necesitan al menos {bb_period} puntos históricos para calcular Bandas Bollinger. "
                f"Cargá un CSV con historial o esperá a que se acumule el historial de la sesión.")
    else:
        st.warning("No se pueden obtener precios de GD30 y/o AL30 de data912.com para calcular el ratio.")

# ─── Input manual para simulación ────────────────────────────────────────────
st.divider()
st.markdown("#### ✏️ Agregar punto manual al historial")
with st.form("add_manual"):
    m1, m2, m3 = st.columns(3)
    with m1:
        manual_gd30 = st.number_input("GD30 (USD)", value=float(p_gd30 or 55.0), step=0.01, format="%.4f")
    with m2:
        manual_al30 = st.number_input("AL30 (USD)", value=float(p_al30 or 53.0), step=0.01, format="%.4f")
    with m3:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("➕ Agregar", use_container_width=True)

    if submitted and manual_gd30 > 0 and manual_al30 > 0:
        st.session_state.ratio_history.append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ratio": manual_gd30 / manual_al30,
            "gd30": manual_gd30,
            "al30": manual_al30,
        })
        st.success(f"Punto agregado. Historial: {len(st.session_state.ratio_history)} puntos.")
        st.rerun()
