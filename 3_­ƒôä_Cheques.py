"""
pages/3_📄_Cheques.py
Calculadora de Descuento de Cheques de Pago Diferido.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header

st.set_page_config(page_title="Descuento de Cheques", page_icon="📄", layout="wide")
apply_style()
page_header("Descuento de Cheques", subtitle="Calculadora · Cheques de Pago Diferido (CPD)", icon="◈")

tab_directo, tab_inverso = st.tabs(["🧮 Calcular precio neto", "🔍 Calcular tasa implícita"])

# ──────────────────────────────────────────────────────────────────────────────
with tab_directo:
    st.markdown("#### Parámetros del cheque")

    d1, d2 = st.columns(2)

    with d1:
        vn = st.number_input("Valor Nominal (VN) del cheque ($)", value=100_000.0,
                              min_value=1.0, step=1_000.0, format="%.2f")
        dias = st.number_input("Días al vencimiento", value=30, min_value=1, max_value=365, step=1)
        tasa_descuento = st.number_input("Tasa de descuento TNA (%)", value=60.0,
                                          min_value=0.0, max_value=5000.0, step=0.5, format="%.4f")
        modalidad = st.selectbox("Modalidad de descuento",
                                  ["Sobre valor nominal (interés simple)",
                                   "Sobre precio (valor presente)"])

    with d2:
        st.markdown("#### Costos adicionales")
        com_alyc = st.number_input("Comisión ALyC (%)", value=0.30, min_value=0.0, step=0.05, format="%.4f")
        iva_com = st.number_input("IVA sobre comisión (%)", value=21.0, min_value=0.0, step=1.0)
        ret_iibb = st.number_input("Retención IIBB (%)", value=0.0, min_value=0.0, step=0.05, format="%.4f",
                                    help="Varía por provincia")
        sello = st.number_input("Impuesto de sello (%)", value=0.0, min_value=0.0, step=0.01, format="%.4f")

    st.divider()

    # ─── Cálculo ──────────────────────────────────────────────────────────────
    tna_dec = tasa_descuento / 100
    t = dias / 365

    if modalidad.startswith("Sobre valor nominal"):
        # Descuento lineal sobre VN
        descuento_financiero = vn * tna_dec * t
        precio_bruto = vn - descuento_financiero
    else:
        # Valor presente (tasa sobre precio)
        precio_bruto = vn / (1 + tna_dec * t)
        descuento_financiero = vn - precio_bruto

    com_monto = precio_bruto * (com_alyc / 100) * (1 + iva_com / 100)
    iibb_monto = precio_bruto * (ret_iibb / 100)
    sello_monto = vn * (sello / 100)

    precio_neto = precio_bruto - com_monto - iibb_monto - sello_monto

    # Tasa real implícita (lo que realmente recibe el cedente)
    if precio_neto > 0 and dias > 0:
        tna_real = (vn / precio_neto - 1) / t * 100
    else:
        tna_real = 0.0

    # ─── Resultados ──────────────────────────────────────────────────────────
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Precio bruto", f"${precio_bruto:,.2f}")
    r2.metric("Precio neto (a recibir)", f"${precio_neto:,.2f}")
    r3.metric("Descuento financiero", f"${descuento_financiero:,.2f}")
    r4.metric("TNA real (al cedente)", f"{tna_real:.4f}%")

    st.markdown("##### 📋 Desglose completo")
    st.markdown(f"""
    | Concepto | Monto ($) |
    |---|---|
    | Valor nominal cheque | **${vn:,.4f}** |
    | Descuento financiero ({tasa_descuento:.2f}% TNA × {dias} días) | −${descuento_financiero:,.4f} |
    | Precio bruto | **${precio_bruto:,.4f}** |
    | Comisión ALyC ({com_alyc:.4f}% + IVA {iva_com:.0f}%) | −${com_monto:,.4f} |
    | Retención IIBB ({ret_iibb:.4f}%) | −${iibb_monto:,.4f} |
    | Impuesto de sello ({sello:.4f}%) | −${sello_monto:,.4f} |
    | **PRECIO NETO A RECIBIR** | **${precio_neto:,.4f}** |
    | TNA real implícita | **{tna_real:.4f}%** |
    """)

    # ─── Tabla comparativa de plazos ─────────────────────────────────────────
    st.divider()
    st.markdown("#### 📊 Comparativa por plazo")
    plazos_chq = [15, 30, 45, 60, 90, 120, 180, 270, 365]
    rows = []
    for p in plazos_chq:
        t_p = p / 365
        if modalidad.startswith("Sobre valor nominal"):
            pb = vn - vn * tna_dec * t_p
        else:
            pb = vn / (1 + tna_dec * t_p)
        pn = pb - pb*(com_alyc/100)*(1+iva_com/100) - pb*(ret_iibb/100) - vn*(sello/100)
        tna_r = (vn/pn - 1)/t_p*100 if pn > 0 else 0
        rows.append({
            "Días": p,
            "Precio bruto ($)": f"${pb:,.2f}",
            "Precio neto ($)": f"${pn:,.2f}",
            "Descuento neto ($)": f"${vn-pn:,.2f}",
            "TNA real (%)": f"{tna_r:.2f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
with tab_inverso:
    st.markdown("#### Calcular tasa implícita dado precio")
    st.caption("¿A qué tasa efectivamente te están descontando el cheque?")

    i1, i2, i3 = st.columns(3)
    with i1:
        vn_inv = st.number_input("Valor Nominal ($)", value=100_000.0,
                                  step=1000.0, format="%.2f", key="vn_inv")
    with i2:
        precio_inv = st.number_input("Precio neto recibido ($)", value=92_000.0,
                                      step=100.0, format="%.2f", key="px_inv")
    with i3:
        dias_inv = st.number_input("Días al vencimiento", value=60,
                                    min_value=1, max_value=365, step=1, key="d_inv")

    if vn_inv > precio_inv > 0 and dias_inv > 0:
        t_inv = dias_inv / 365
        tna_inv = (vn_inv / precio_inv - 1) / t_inv * 100
        tem_inv = ((1 + tna_inv/100)**(1/12) - 1) * 100
        tea_inv = ((1 + tna_inv/100)**1 - 1) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("TNA implícita", f"{tna_inv:.4f}%")
        c2.metric("TEM equiv.", f"{tem_inv:.4f}%")
        c3.metric("Costo financiero", f"${vn_inv - precio_inv:,.2f}", delta=f"{(vn_inv/precio_inv-1)*100:.2f}%")
    else:
        st.info("El valor nominal debe ser mayor que el precio recibido.")
