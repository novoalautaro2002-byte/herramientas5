"""
pages/7_📈_Bonos_CER.py
Bonos indexados por CER: TIR Real (Newton-Raphson).
Metodología: deflactar flujos por CER, resolver NPV = 0.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header, fetch_bonds, fetch_cer, get_cer_value

st.set_page_config(page_title="Bonos CER", page_icon="📈", layout="wide")
apply_style()
page_header("Bonos CER", subtitle="Instrumentos CER — TX / DICP / PARP / TZXY", icon="◎")

# ─── Instrumentos CER conocidos ───────────────────────────────────────────────
# Formato: ticker → {nombre, vencimiento, cupon_real_pct, tipo}
CER_BONDS = {
    # Zero-coupon (TZXY series) — 2025
    "TZX25": {"nombre": "Boncer Zero 2025", "vcto": date(2025, 12, 18), "cupon": 0.0, "tipo": "ZC"},
    "TZX26": {"nombre": "Boncer Zero 2026", "vcto": date(2026, 6, 30), "tipo": "ZC", "cupon": 0.0},
    # TX series (Boncer amortizables) — tasa real positiva
    "TX26":  {"nombre": "TX26 — Boncer 2026", "vcto": date(2026,  7,  9), "cupon": 2.00, "tipo": "AM"},
    "TX27":  {"nombre": "TX27 — Boncer 2027", "vcto": date(2027,  7,  9), "cupon": 2.00, "tipo": "AM"},
    "TX28":  {"nombre": "TX28 — Boncer 2028", "vcto": date(2028,  7,  9), "cupon": 2.00, "tipo": "AM"},
    # Cuasi-pares / DICP / PARP
    "DICP":  {"nombre": "DICP — Disc. Pesos CER", "vcto": date(2033,  12, 31), "cupon": 5.83, "tipo": "AM"},
    "PARP":  {"nombre": "PARP — Par Pesos CER",   "vcto": date(2038,  12, 31), "cupon": 2.00, "tipo": "AM"},
}

# ─── Fetch data ───────────────────────────────────────────────────────────────
col_ref, _ = st.columns([1, 4])
with col_ref:
    if st.button("🔄 Actualizar"):
        fetch_bonds.clear()
        fetch_cer.clear()
        st.rerun()

with st.spinner("Cargando precios y CER…"):
    bond_prices = fetch_bonds()
    cer_data = fetch_cer()

hoy = date.today()
cer_hoy = get_cer_value(hoy, cer_data)

if cer_hoy:
    st.caption(f"📅 CER hoy ({hoy.strftime('%d/%m/%Y')}): **{cer_hoy:,.4f}**")
else:
    st.warning("No se pudo obtener el CER de hoy desde ArgentinaDatos.")

# ─── Metodología ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ Metodología TIR Real"):
    st.markdown("""
    **Fórmula:**  
    Los flujos nominales futuros se **deflactan** por el ratio CER:
    ```
    flujo_real_i = flujo_nominal_i × (CER_hoy / CER_fecha_i)
    ```
    Luego se resuelve Newton-Raphson sobre precio_real:
    ```
    precio_real = Σ flujo_real_i / (1 + r)^t_i
    precio_real = precio_pesos / CER_hoy × cerBase
    ```
    donde `r` = TIR Real (Act/365.25).
    """)

st.divider()

# ─── Panel de bonos CER ───────────────────────────────────────────────────────
st.markdown("#### 📊 Bonos CER — Precios y Rendimientos estimados")

rows = []
for ticker, info in CER_BONDS.items():
    p_pesos = bond_prices.get(ticker)
    row = {
        "Ticker": ticker,
        "Instrumento": info["nombre"],
        "Vencimiento": info["vcto"].strftime("%d/%m/%Y"),
        "Tipo": info["tipo"],
        "Precio ($)": f"${p_pesos:,.2f}" if p_pesos else "—",
        "TIR Real (%)": "—",
        "Días": (info["vcto"] - hoy).days,
    }
    rows.append(row)

if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ─── Calculadora individual ────────────────────────────────────────────────────
st.markdown("#### 🧮 Calculadora de TIR Real")
st.caption("Seleccioná un bono y calculá la TIR real ajustada por CER.")

calc_col, res_col = st.columns([1, 1.2])

with calc_col:
    ticker_cer = st.selectbox("Instrumento", list(CER_BONDS.keys()), index=0)
    info_cer = CER_BONDS[ticker_cer]

    p_live_cer = bond_prices.get(ticker_cer)
    usar_live_cer = st.checkbox("Usar precio de mercado", value=bool(p_live_cer))

    precio_pesos = st.number_input(
        "Precio en pesos ($)",
        value=float(p_live_cer or 100.0),
        min_value=0.01, step=1.0, format="%.4f"
    )

    cer_base = st.number_input(
        "CER base del bono (emision)",
        value=100.0, min_value=0.001, step=1.0, format="%.4f",
        help="CER en la fecha de emisión del bono (ver prospecto)."
    )

    if cer_hoy:
        cer_input = cer_hoy
        st.caption(f"CER vigente (hoy): **{cer_hoy:,.4f}**")
    else:
        cer_input = st.number_input("CER vigente (manual)", value=1000.0, step=1.0, format="%.4f")

    # Para zero coupon: precio real = precio_pesos / (CER_hoy / CER_base)
    # = precio_pesos × CER_base / CER_hoy
    factor_cer = cer_input / cer_base if cer_base > 0 else 1.0
    precio_real_ajustado = precio_pesos / factor_cer

    st.caption(f"Factor CER: **{factor_cer:.6f}** → precio deflactado: **${precio_real_ajustado:.4f}**")

with res_col:
    vcto = info_cer["vcto"]
    dias_vcto = (vcto - hoy).days

    if dias_vcto <= 0:
        st.error("Este instrumento ya venció.")
    elif precio_pesos > 0 and cer_input > 0:
        if info_cer["tipo"] == "ZC":
            # Zero coupon: TIR real directa por compounding Act/365.25
            # precio_real = 100 / (1 + r)^t  →  r = (100/precio_real)^(1/t) - 1
            t = dias_vcto / 365.25
            if t > 0 and precio_real_ajustado > 0:
                tir_real = (100 / precio_real_ajustado)**(1/t) - 1
                tir_real_pct = tir_real * 100

                r1, r2 = st.columns(2)
                r1.metric("TIR Real (TEA)", f"{tir_real_pct:.4f}%",
                          help="Tasa Efectiva Anual real ajustada por CER")
                r2.metric("Días al vencimiento", f"{dias_vcto}")
                st.metric("Precio deflactado", f"${precio_real_ajustado:.4f}")
                st.metric("Retorno real total", f"{(100/precio_real_ajustado - 1)*100:.4f}%")
        else:
            # Bonos amortizables — Newton-Raphson simplificado
            # Generamos flujos nominales aproximados y deflactamos
            # Para cálculo real riguroso: necesitar flujos con CER forward (inflación esperada)
            # Aquí usamos una aproximación: flujos CER de hoy hacia adelante
            cpn_rate = info_cer.get("cupon", 0.0) / 100
            # Semi-annual coupons on outstanding
            from utils import _semiannual_dates
            # Aproximación: generar flujos semestrales hasta vencimiento
            vcto_dt = info_cer["vcto"]
            # Generamos fechas semi-anuales de hoy hacia adelante
            cf_dates = _semiannual_dates(
                date(hoy.year, 6 if hoy.month <= 6 else 12, 31),
                vcto_dt
            )
            if not cf_dates or cf_dates[-1] < vcto_dt:
                cf_dates.append(vcto_dt)

            # Flujos reales (sin inflación forward): simplificamos deflactando al CER de hoy
            # Esto es una aproximación conservadora — para TIR exacta necesitamos inflación esperada
            outstanding = 100.0
            n_flows = len(cf_dates)
            amort_per = 100.0 / n_flows if n_flows > 0 else 0

            flows_real = []
            for cf_date in cf_dates:
                cpn = outstanding * cpn_rate / 2  # semi-annual
                amort = amort_per
                nominal = cpn + amort
                # Deflactar: CER futuro ≈ CER hoy (sin proyección de inflación)
                # Para TIR real: precio_real = Σ flujo_real / (1+r)^t
                t = (cf_date - hoy).days / 365.25
                flows_real.append((cf_date, nominal))
                outstanding -= amort

            # Newton-Raphson sobre precio real
            precio_r = precio_real_ajustado

            def npv_r(r):
                return sum(m / (1+r)**((d-hoy).days/365.25) for d, m in flows_real) - precio_r

            def dnpv_r(r):
                return sum(-(d-hoy).days/365.25 * m / (1+r)**((d-hoy).days/365.25 + 1) for d, m in flows_real)

            r_val = 0.05
            for _ in range(300):
                fv, dfv = npv_r(r_val), dnpv_r(r_val)
                if abs(dfv) < 1e-14: break
                r_new = r_val - fv/dfv
                r_new = max(min(r_new, 5.0), -0.99)
                if abs(r_new - r_val) < 1e-10: r_val = r_new; break
                r_val = r_new

            tir_real_pct = r_val * 100

            r1, r2 = st.columns(2)
            r1.metric("TIR Real aprox. (TEA)", f"{tir_real_pct:.4f}%")
            r2.metric("Días al vencimiento", f"{dias_vcto}")
            st.caption("⚠️ Aproximación: no proyecta inflación CER forward. Para TIR exacta usar rendimientos.co")
    else:
        st.info("Ingresá precio y CER para calcular.")
