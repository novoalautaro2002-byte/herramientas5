"""
pages/5_◆_LECAP_BONCAP.py
Calculadora y tracker de LECAP / BONCAP.
"""
import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header, fetch_notes

st.set_page_config(page_title="LECAP / BONCAP", page_icon="◆", layout="wide")
apply_style()
page_header("LECAP / BONCAP", subtitle="Letras y Bonos de Capitalización en Pesos", icon="◆")

# Convención: precio = VR / (1 + TEM)^(dias/30)
# TEM = (VR/precio)^(30/dias) - 1

def calc_tem_from_price(vr: float, precio: float, dias: int) -> float | None:
    if precio <= 0 or dias <= 0:
        return None
    return (vr / precio)**(30 / dias) - 1

def calc_price_from_tem(vr: float, tem: float, dias: int) -> float:
    return vr / (1 + tem)**(dias / 30)

def tem_to_tna(tem: float) -> float:
    return tem * 12  # TNA simple = TEM × 12

def tem_to_tea(tem: float) -> float:
    return (1 + tem)**12 - 1

def tna_to_tem(tna: float) -> float:
    return tna / 12

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_calc, tab_market = st.tabs(["🧮 Calculadora", "📊 Precios de Mercado"])

# ─────────────────────────────────────────────────────────────────────────────
with tab_calc:
    st.markdown("#### Precio / Rendimiento LECAP o BONCAP")

    mode = st.radio("¿Qué querés calcular?",
                    ["→ Rendimiento dado precio (TEM, TNA, TEA)",
                     "→ Precio dado rendimiento (TEM o TNA)"],
                    horizontal=True)

    c1, c2 = st.columns([1, 1])

    with c1:
        vr = st.number_input("Valor Residual (VR) al vencimiento ($)",
                              value=1.0, min_value=0.001, step=0.001, format="%.6f",
                              help="Para LECAP: generalmente = $1. Para BONCAP puede diferir.")
        hoy = date.today()
        fecha_vcto = st.date_input("Fecha de vencimiento", value=date(hoy.year, hoy.month + 3 if hoy.month <= 9 else hoy.month - 9, 1),
                                   min_value=hoy)
        dias_al_vcto = (fecha_vcto - hoy).days
        st.caption(f"📅 Días al vencimiento: **{dias_al_vcto}** días ({dias_al_vcto/30:.1f} meses)")

    with c2:
        if mode.startswith("→ Rendimiento"):
            precio_input = st.number_input("Precio de compra / cotización ($)",
                                            value=0.85, min_value=0.0001, step=0.0001,
                                            format="%.6f",
                                            help="Ingresá el precio en las mismas unidades que el VR")
            if precio_input > 0 and dias_al_vcto > 0:
                tem = calc_tem_from_price(vr, precio_input, dias_al_vcto)
                tna = tem_to_tna(tem)
                tea = tem_to_tea(tem)

                st.markdown("#### Rendimiento")
                r1, r2, r3 = st.columns(3)
                r1.metric("TEM", f"{tem*100:.4f}%")
                r2.metric("TNA (TEM × 12)", f"{tna*100:.4f}%")
                r3.metric("TEA", f"{tea*100:.4f}%")

                st.divider()
                st.markdown(f"""
                | Concepto | Valor |
                |---|---|
                | Precio | ${precio_input:.6f} |
                | VR | ${vr:.6f} |
                | Días | {dias_al_vcto} |
                | Retorno total | {(vr/precio_input - 1)*100:.4f}% |
                | **TEM** | **{tem*100:.6f}%** |
                | TNA simple | {tna*100:.4f}% |
                | TEA | {tea*100:.4f}% |
                """)
        else:
            tem_input_pct = st.number_input("TEM (%)", value=5.0, min_value=0.0, step=0.1, format="%.4f",
                                             help="Tasa Efectiva Mensual")
            tna_input_pct = st.number_input("O bien, TNA simple (%)", value=60.0, min_value=0.0, step=0.5, format="%.4f",
                                             help="Se usa TEM = TNA/12")
            usar_tem = st.radio("Usar", ["TEM directa", "TNA → TEM"], horizontal=True)

            if usar_tem == "TEM directa":
                tem_calc = tem_input_pct / 100
            else:
                tem_calc = tna_to_tem(tna_input_pct / 100)

            precio_calc = calc_price_from_tem(vr, tem_calc, dias_al_vcto)
            tea_calc = tem_to_tea(tem_calc)

            st.markdown("#### Precio calculado")
            st.metric("Precio", f"${precio_calc:.6f}")
            st.metric("TEA equivalente", f"{tea_calc*100:.4f}%")
            st.metric("Retorno total al vencimiento", f"{(vr/precio_calc - 1)*100:.4f}%")

    # ─── Tabla de sensibilidad TEM vs precio ─────────────────────────────────
    st.divider()
    st.markdown("#### 📊 Sensibilidad TEM → Precio")
    if dias_al_vcto > 0:
        import numpy as np
        tems = np.arange(2.0, 14.0, 0.5)  # TEM de 2% a 13.5%
        rows = []
        for t_pct in tems:
            p = calc_price_from_tem(vr, t_pct/100, dias_al_vcto)
            rows.append({
                "TEM (%)": f"{t_pct:.2f}%",
                "TNA (%)": f"{t_pct*12:.2f}%",
                "TEA (%)": f"{((1+t_pct/100)**12-1)*100:.2f}%",
                f"Precio (VR={vr:.3f})": f"${p:.6f}",
                "Retorno total (%)": f"{(vr/p-1)*100:.4f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
with tab_market:
    st.markdown("#### Precios de mercado — LECAP / BONCAP")
    st.caption("Fuente: data912.com/live/arg_notes")

    col_ref, _ = st.columns([1, 4])
    with col_ref:
        if st.button("🔄 Actualizar", key="ref_notes"):
            fetch_notes.clear()
            st.rerun()

    with st.spinner("Cargando precios…"):
        notes = fetch_notes()

    if not notes:
        st.warning("No se encontraron instrumentos. Verificá la conexión a data912.com")
    else:
        hoy = date.today()
        rows = []
        for ticker, precio in sorted(notes.items()):
            # Intentar parsear fecha del ticker (ej: S14F5 = S14-Feb-2025)
            # Formato BYMA para LECAP: SDDMMYY
            row = {
                "Ticker": ticker,
                "Precio ($)": f"${precio:.4f}",
                "TEM (%)": "—",
                "TNA (%)": "—",
                "TEA (%)": "—",
            }
            rows.append(row)

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("💡 Para calcular TEM/TNA de un instrumento específico, usá la tab 🧮 Calculadora ingresando el precio y la fecha de vencimiento.")
