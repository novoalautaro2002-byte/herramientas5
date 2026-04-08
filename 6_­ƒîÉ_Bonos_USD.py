"""
pages/6_🌐_Bonos_USD.py
Bonos Soberanos en USD: TIR, TNA, Duración.
Newton-Raphson con flujos hardcodeados (canje 2020).
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header, fetch_bonds, get_bond_cashflows, newton_raphson_tir, fmt_pct

st.set_page_config(page_title="Bonos Soberanos USD", page_icon="🌐", layout="wide")
apply_style()
page_header("Bonos Soberanos USD", subtitle="Bonares & Globales · Canje 2020", icon="◇")

st.warning("⚠️ Los flujos de fondos están hardcodeados basados en los prospectos del canje 2020. "
           "Verificar siempre contra [rendimientos.co](https://rendimientos.co) ante cualquier discrepancia.")

# ─── Tickers disponibles ──────────────────────────────────────────────────────
BONARES  = ["AL29", "AL30", "AL35", "AL38", "AL41"]
GLOBALES = ["GD29", "GD30", "GD35", "GD38", "GD41", "GD46"]
ALL_TICKERS = BONARES + GLOBALES

col_ref, _ = st.columns([1, 4])
with col_ref:
    if st.button("🔄 Actualizar precios"):
        fetch_bonds.clear()
        st.rerun()

with st.spinner("Cargando precios de mercado…"):
    prices = fetch_bonds()

# ─── Tabla resumen con TIR ────────────────────────────────────────────────────
st.markdown("#### 📊 Panel de Bonos")

rows = []
for t in ALL_TICKERS:
    p = prices.get(t)
    cfs = get_bond_cashflows(t)
    if p and cfs:
        tna, tea, dur_mod = newton_raphson_tir(p, cfs)
        rows.append({
            "Ticker": t,
            "Tipo": "Bonar" if t.startswith("A") else "Global",
            "Precio (USD)": f"{p:.4f}",
            "TNA (%)": f"{tna*100:.2f}%" if tna else "—",
            "TEA (%)": f"{tea*100:.2f}%" if tea else "—",
            "Dur. Mod.": f"{dur_mod:.2f}" if dur_mod else "—",
        })
    else:
        rows.append({
            "Ticker": t,
            "Tipo": "Bonar" if t.startswith("A") else "Global",
            "Precio (USD)": f"{p:.4f}" if p else "—",
            "TNA (%)": "—", "TEA (%)": "—", "Dur. Mod.": "—",
        })

if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ─── Calculadora individual ────────────────────────────────────────────────────
st.markdown("#### 🧮 Calculadora individual")
st.caption("Seleccioná un bono, ajustá el precio (o usá el de mercado) y calculá TIR/Duración.")

col_sel, col_res = st.columns([1, 1.5])

with col_sel:
    ticker_sel = st.selectbox("Bono", ALL_TICKERS, index=1)  # default GD30 aprox
    p_live = prices.get(ticker_sel)

    usar_live = st.checkbox("Usar precio de mercado", value=bool(p_live), key="usar_live_b")
    if usar_live and p_live:
        precio_input = st.number_input("Precio (USD, por cada 100 VN)", value=float(p_live),
                                        min_value=0.01, step=0.01, format="%.4f", key="p_bono")
    else:
        precio_input = st.number_input("Precio (USD, por cada 100 VN)", value=50.0,
                                        min_value=0.01, step=0.01, format="%.4f", key="p_bono_m")

    accrued = st.number_input("Interés corrido (dejar 0 si precio ya es sucio)", value=0.0,
                               step=0.01, format="%.4f",
                               help="El precio de data912 generalmente es precio limpio. "
                                    "Sumale el interés corrido para obtener precio sucio.")
    precio_sucio = precio_input + accrued

    cfs = get_bond_cashflows(ticker_sel)
    futuros = [(d, m) for d, m in cfs if d > date.today()]

    st.caption(f"Flujos futuros: {len(futuros)} pagos — "
               f"próximo vencimiento: {min(d for d,_ in futuros).strftime('%d/%m/%Y') if futuros else '—'}")

with col_res:
    if precio_sucio > 0 and cfs:
        tna, tea, dur_mod = newton_raphson_tir(precio_sucio, cfs)

        if tna is not None:
            r1, r2 = st.columns(2)
            r1.metric("TNA", f"{tna*100:.4f}%",
                      help="Tasa Nominal Anual con capitalización semestral")
            r2.metric("TEA", f"{tea*100:.4f}%",
                      help="Tasa Efectiva Anual = (1 + TNA/2)² − 1")

            r3, r4 = st.columns(2)
            r3.metric("Duración Modificada", f"{dur_mod:.4f}",
                      help="Sensibilidad del precio ante variación de 1% en la TIR")
            r4.metric("Precio sucio input", f"U$S {precio_sucio:.4f}")

            # DV01 aprox.
            dv01 = dur_mod * precio_sucio / 100 / 100
            st.metric("DV01 (por 100 VN)", f"${dv01:.4f}",
                      help="Variación en precio ante 1 bps de cambio en TIR")
        else:
            st.error("No convergió el cálculo de TIR. Verificá el precio.")
    else:
        st.info("Ingresá el precio para calcular.")

# ─── Tabla de flujos de fondos ─────────────────────────────────────────────────
if ticker_sel and cfs:
    with st.expander(f"📋 Ver flujos de fondos — {ticker_sel}"):
        today = date.today()
        cf_rows = []
        for d, m in cfs:
            cf_rows.append({
                "Fecha": d.strftime("%d/%m/%Y"),
                "Monto (por 100 VN)": f"${m:.6f}",
                "Estado": "⏳ Futuro" if d > today else "✅ Pagado",
            })
        df_cf = pd.DataFrame(cf_rows)
        st.dataframe(df_cf, use_container_width=True, hide_index=True)

# ─── Curva de rendimientos ─────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📈 Curva de Rendimientos USD")

curve_rows = {"Ticker": [], "Duration": [], "TNA": [], "Tipo": []}
for t in ALL_TICKERS:
    p = prices.get(t)
    cfs_t = get_bond_cashflows(t)
    if p and cfs_t:
        tna_t, _, dur_t = newton_raphson_tir(p, cfs_t)
        if tna_t and dur_t:
            curve_rows["Ticker"].append(t)
            curve_rows["Duration"].append(dur_t)
            curve_rows["TNA"].append(tna_t * 100)
            curve_rows["Tipo"].append("Bonar" if t.startswith("A") else "Global")

if curve_rows["Ticker"]:
    fig = go.Figure()
    for tipo, color in [("Bonar", "#3a6fd8"), ("Global", "#22d68a")]:
        mask = [i for i, tp in enumerate(curve_rows["Tipo"]) if tp == tipo]
        x = [curve_rows["Duration"][i] for i in mask]
        y = [curve_rows["TNA"][i] for i in mask]
        labels = [curve_rows["Ticker"][i] for i in mask]
        if x:
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="markers+text",
                name=tipo,
                text=labels, textposition="top center",
                marker=dict(size=10, color=color),
            ))

    fig.update_layout(
        title="Curva de Rendimientos — TNA vs Duración Modificada",
        xaxis_title="Duración Modificada (años)",
        yaxis_title="TNA (%)",
        paper_bgcolor="#0d1b2e",
        plot_bgcolor="#122540",
        font=dict(color="#f0f4ff", family="Inter"),
        legend=dict(bgcolor="#1a3358", bordercolor="#2a4a7a"),
        xaxis=dict(gridcolor="#2a4a7a"),
        yaxis=dict(gridcolor="#2a4a7a"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay suficientes datos para graficar la curva. Verificá conexión a data912.com")
