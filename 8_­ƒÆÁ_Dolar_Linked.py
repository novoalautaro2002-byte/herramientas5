"""
pages/8_💵_Dolar_Linked.py
Bonos Dólar Linked — Tasa de devaluación implícita.
"""
import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header, fetch_bonds, fetch_dolar

st.set_page_config(page_title="Dólar Linked", page_icon="💵", layout="wide")
apply_style()
page_header("Dólar Linked", subtitle="Instrumentos indexados al tipo de cambio oficial", icon="◐")

st.markdown("""
Los bonos **dólar linked** pagan en pesos pero su capital y cupones están indexados al tipo de cambio oficial ($/USD).
La **tasa de devaluación implícita** se obtiene comparando el rendimiento del instrumento con una tasa libre de riesgo en pesos.
""")

# ─── Instrumentos dólar linked conocidos ─────────────────────────────────────
DL_BONDS = {
    "TV25": {"nombre": "TV25 — T2V25", "vcto": date(2025, 4, 30), "cupon": 0.0, "tipo": "ZC"},
    "TV26": {"nombre": "TV26 — T2V26", "vcto": date(2026, 4, 30), "cupon": 0.0, "tipo": "ZC"},
    "TV27": {"nombre": "TV27 — T2V27", "vcto": date(2027, 4, 30), "cupon": 0.0, "tipo": "ZC"},
    "D2X5": {"nombre": "D2X5 — Dólar Linked 2025", "vcto": date(2025, 12, 31), "cupon": 2.0, "tipo": "AM"},
    "D2X6": {"nombre": "D2X6 — Dólar Linked 2026", "vcto": date(2026, 12, 31), "cupon": 2.0, "tipo": "AM"},
}

col_ref, _ = st.columns([1, 4])
with col_ref:
    if st.button("🔄 Actualizar"):
        fetch_bonds.clear()
        fetch_dolar.clear()
        st.rerun()

with st.spinner("Cargando…"):
    bond_prices = fetch_bonds()
    fx = fetch_dolar()

hoy = date.today()
tc_oficial = None
if "oficial" in fx:
    tc_oficial = float(fx["oficial"].get("venta", 0) or 0)

if tc_oficial:
    st.metric("TC Oficial (venta)", f"${tc_oficial:,.2f}")
else:
    st.warning("No se pudo obtener TC Oficial de dolarapi.com")

st.divider()

# ─── Calculadora ──────────────────────────────────────────────────────────────
tab_impl, tab_price = st.tabs(["📉 Devaluación implícita", "🧮 Precio dado devaluación"])

with tab_impl:
    st.markdown("#### Calcular tasa de devaluación implícita en el precio")
    st.caption("Para un bono ZC: precio_USD_implicito = precio_pesos / TC_esperado")

    c1, c2 = st.columns(2)
    with c1:
        ticker_dl = st.selectbox("Instrumento", list(DL_BONDS.keys()), key="ticker_dl")
        info_dl = DL_BONDS[ticker_dl]
        p_live = bond_prices.get(ticker_dl)

        precio_pesos = st.number_input("Precio en pesos ($)", value=float(p_live or 100.0),
                                        step=0.01, format="%.4f", key="p_dl")
        tc_actual = st.number_input("TC Oficial actual ($/USD)", value=float(tc_oficial or 1000.0),
                                     step=1.0, format="%.2f", key="tc_dl")
        tasa_libre_riesgo = st.number_input("Tasa libre de riesgo en pesos (TEA %)",
                                             value=50.0, step=1.0, format="%.4f",
                                             help="Tasa de referencia en pesos (ej: LECAP o caución más corta)")

    with c2:
        vcto = info_dl["vcto"]
        dias = (vcto - hoy).days

        if dias > 0 and precio_pesos > 0 and tc_actual > 0:
            t = dias / 365.0

            # El bono tiene VR = 100 en dólares linked
            # precio_pesos = VR_USD × TC_futuro_esperado / (1 + r_dl)^t
            # Para ZC con r_dl = 0 (solo indexa al TC): 
            # precio_pesos / TC_actual = precio_en_usd_implicito
            precio_usd_impl = precio_pesos / tc_actual

            # Tasa de devaluación implícita (TEA): 
            # precio_usd_impl = 100 / (1 + dev)^t  →  dev = (100/precio_usd_impl)^(1/t) - 1
            if precio_usd_impl > 0:
                dev_impl_tea = (100.0 / precio_usd_impl)**(1/t) - 1
            else:
                dev_impl_tea = 0

            # Tasa de corte: diferencia entre tasa pesos y devaluación implícita
            # Si tasa_pesos > devaluación implícita → bono DL barato (conviene)
            spread_carry = (1 + tasa_libre_riesgo/100) / (1 + dev_impl_tea) - 1
            carry_positivo = spread_carry > 0

            r1, r2 = st.columns(2)
            r1.metric("Precio USD implícito", f"U$S {precio_usd_impl:.4f}",
                      help="precio_pesos / TC_oficial")
            r2.metric("Devaluación implícita (TEA)", f"{dev_impl_tea*100:.2f}%")

            r3, r4 = st.columns(2)
            r3.metric("Carry vs tasa pesos", f"{spread_carry*100:.2f}%",
                      delta="✅ Carry positivo (conviene pesos)" if carry_positivo else "❌ Carry negativo",
                      delta_color="normal")
            r4.metric("Días al vencimiento", f"{dias}")

            st.info(
                f"Si la devaluación real es **menor** al {dev_impl_tea*100:.2f}% TEA implícito, "
                f"el bono queda **sobrevaluado** (el TC no alcanzará el implícito). "
                f"Si es **mayor**, el bono queda **subvaluado**."
            )
        else:
            st.info("Completá los campos para calcular.")

with tab_price:
    st.markdown("#### Calcular precio dado escenario de devaluación")

    cp1, cp2 = st.columns(2)
    with cp1:
        ticker_sc = st.selectbox("Instrumento", list(DL_BONDS.keys()), key="ticker_sc")
        info_sc = DL_BONDS[ticker_sc]
        vcto_sc = info_sc["vcto"]
        dias_sc = (vcto_sc - hoy).days

        tc_base = st.number_input("TC Oficial hoy ($/USD)", value=float(tc_oficial or 1000.0),
                                   step=1.0, format="%.2f", key="tc_sc")
        dev_escenario = st.number_input("Devaluación esperada (TEA %)", value=30.0,
                                         step=1.0, format="%.2f", key="dev_sc",
                                         help="Escenario de devaluación anual que esperás")

    with cp2:
        if dias_sc > 0 and tc_base > 0:
            t_sc = dias_sc / 365.0
            # TC esperado
            tc_esperado = tc_base * (1 + dev_escenario/100)**t_sc
            # Precio justo del bono (ZC, VR = 100 USD)
            precio_justo = 100.0 * tc_esperado  # en pesos

            # Si hay cupón: precio más complejo
            precio_actual = bond_prices.get(ticker_sc)

            r1, r2 = st.columns(2)
            r1.metric("TC esperado al vencimiento", f"${tc_esperado:,.2f}")
            r2.metric("Precio justo (pesos)", f"${precio_justo:,.2f}")

            if precio_actual:
                upside = (precio_justo / precio_actual - 1) * 100
                st.metric("Precio de mercado actual", f"${precio_actual:,.2f}",
                          delta=f"{upside:+.2f}% vs precio justo",
                          delta_color="normal")
        else:
            st.info("Completá los campos.")

# ─── Tabla comparativa ────────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📊 Comparativa de instrumentos DL")

rows = []
for ticker, info in DL_BONDS.items():
    p = bond_prices.get(ticker)
    dias_t = (info["vcto"] - hoy).days
    row = {
        "Ticker": ticker,
        "Vencimiento": info["vcto"].strftime("%d/%m/%Y"),
        "Días": dias_t,
        "Precio ($)": f"${p:,.2f}" if p else "—",
    }
    if p and tc_oficial and dias_t > 0:
        p_usd = p / tc_oficial
        t = dias_t / 365.0
        dev = (100.0 / p_usd)**(1/t) - 1 if p_usd > 0 else None
        row["Precio USD impl."] = f"U$S {p_usd:.4f}" if p_usd else "—"
        row["Dev. implícita (TEA%)"] = f"{dev*100:.2f}%" if dev else "—"
    else:
        row["Precio USD impl."] = "—"
        row["Dev. implícita (TEA%)"] = "—"
    rows.append(row)

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
