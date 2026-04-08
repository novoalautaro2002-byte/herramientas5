"""
pages/2_⬡_Cauciones.py
Calculadora de Cauciones Bursátiles.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header

st.set_page_config(page_title="Cauciones", page_icon="⬡", layout="wide")
apply_style()
page_header("Cauciones Bursátiles", subtitle="Calculadora · Mercado de Capitales Argentina", icon="⬡")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_calc, tab_inv = st.tabs(["🧮 Calculadora", "🔍 Tasa Implícita"])

# ─── Calculadora directa ──────────────────────────────────────────────────────
with tab_calc:
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### Parámetros")
        modo = st.selectbox("Modalidad", ["Colocador (presta)", "Tomador (toma prestado)"])
        capital = st.number_input("Capital ($)", value=1_000_000.0, min_value=1.0,
                                   step=10_000.0, format="%.2f")
        plazo = st.number_input("Plazo (días)", value=1, min_value=1, max_value=120, step=1)
        tna = st.number_input("TNA (%)", value=40.0, min_value=0.0, max_value=5000.0,
                               step=0.1, format="%.4f")

        # Tasas derivadas
        tem = ((1 + tna / 100) ** (1/12) - 1) * 100
        tea = ((1 + tna / 100) ** 1 - 1) * 100  # TNA = TEA en cauciones (capitalización simple?), ver abajo
        # En cauciones bursátiles la convención es interés simple:
        intereses = capital * (tna / 100) * (plazo / 365)
        total = capital + intereses
        tasa_diaria = tna / 365

        st.divider()
        st.markdown("#### Tasas equivalentes")
        r1, r2, r3 = st.columns(3)
        r1.metric("TNA", f"{tna:.4f}%")
        r2.metric("TEM (comp.)", f"{tem:.4f}%")
        r3.metric("TEA (comp.)", f"{((1+tna/100)**(365/365)-1)*100:.2f}%")
        st.metric("Tasa diaria (lineal)", f"{tasa_diaria:.6f}%")

    with c2:
        st.markdown("#### Resultado")
        st.metric("Intereses", f"${intereses:,.2f}")
        st.metric("Capital inicial", f"${capital:,.2f}")
        st.metric("Total a recibir / pagar", f"${total:,.2f}")
        st.metric(f"Retorno efectivo {plazo} días", f"{intereses/capital*100:.4f}%")

        st.divider()
        st.markdown("##### 📋 Resumen")
        st.markdown(f"""
        | Concepto | Valor |
        |---|---|
        | Modalidad | {modo} |
        | Capital | **${capital:,.2f}** |
        | Plazo | {plazo} días |
        | TNA | {tna:.4f}% |
        | Intereses (base 365) | **${intereses:,.4f}** |
        | **Total** | **${total:,.4f}** |
        """)

    # ─── Tabla de sensibilidad por plazo ──────────────────────────────────────
    st.divider()
    st.markdown("#### 📊 Sensibilidad por plazo")
    import pandas as pd

    plazos_std = [1, 2, 3, 5, 7, 14, 30, 60, 90, 120]
    rows = []
    for p in plazos_std:
        int_p = capital * (tna/100) * (p/365)
        rows.append({
            "Plazo (días)": p,
            "Intereses ($)": f"${int_p:,.2f}",
            "Total ($)": f"${capital + int_p:,.2f}",
            "Retorno (%)": f"{int_p/capital*100:.4f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ─── Tasa implícita ───────────────────────────────────────────────────────────
with tab_inv:
    st.markdown("#### Calcular TNA dada una diferencia de precio")
    st.caption("Útil cuando operás a un precio de pantalla y querés saber la tasa implícita.")

    ci1, ci2, ci3 = st.columns(3)
    with ci1:
        cap_inv = st.number_input("Capital colocado ($)", value=1_000_000.0,
                                   step=10_000.0, format="%.2f", key="cap_inv")
    with ci2:
        total_inv = st.number_input("Total a cobrar ($)", value=1_003_288.0,
                                    step=100.0, format="%.2f", key="total_inv")
    with ci3:
        plazo_inv = st.number_input("Plazo (días)", value=30, min_value=1,
                                    max_value=365, step=1, key="plazo_inv")

    if total_inv > cap_inv > 0 and plazo_inv > 0:
        int_impl = total_inv - cap_inv
        tna_impl = (int_impl / cap_inv) * (365 / plazo_inv) * 100
        tem_impl = ((1 + tna_impl/100)**(1/12) - 1) * 100

        r1, r2, r3 = st.columns(3)
        r1.metric("TNA implícita", f"{tna_impl:.4f}%")
        r2.metric("TEM equivalente", f"{tem_impl:.4f}%")
        r3.metric("Intereses obtenidos", f"${int_impl:,.2f}")
    else:
        st.info("El total debe ser mayor que el capital.")
