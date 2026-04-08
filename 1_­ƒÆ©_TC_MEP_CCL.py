"""
pages/1_💸_TC_MEP_CCL.py
Calculadora de TC / MEP / CCL con costos ALyC y DDMM.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header, fetch_bonds

st.set_page_config(page_title="TC / MEP / CCL", page_icon="💸", layout="wide")
apply_style()
page_header("TC / MEP / CCL", subtitle="Calculadora · Tipo de Cambio Implícito", icon="💸")

bond_prices = fetch_bonds()

# ─── Parámetros globales ───────────────────────────────────────────────────────
with st.expander("⚙️ Parámetros ALyC y DDMM", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        com_pct = st.number_input("Comisión ALyC (%)", value=0.50, min_value=0.0, max_value=5.0, step=0.05, format="%.4f",
                                  help="Porcentaje sobre el monto total ARS operado (por punta)")
    with c2:
        ddmm_pct = st.number_input("DDMM (%)", value=0.0100, min_value=0.0, max_value=1.0, step=0.001, format="%.4f",
                                   help="Derechos de mercado — 0.0100% por punta (BYMA)")
    with c3:
        iva_pct = st.number_input("IVA sobre com. (%)", value=21.0, min_value=0.0, max_value=25.0, step=1.0,
                                  help="IVA sobre la comisión ALyC")

com_total = (com_pct / 100) * (1 + iva_pct / 100) + (ddmm_pct / 100)

st.divider()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_mep, tab_ccl, tab_canje = st.tabs(["📥 MEP (Contado Normal)", "🌐 CCL (Cable)", "🔄 Canje"])

# ─────────────────────────────────────────────────────────────────────────────
with tab_mep:
    st.markdown("##### Compra de USD MEP")
    st.caption("Proceso: comprar bono en ARS → vender bono en USD (cuenta local)")

    mc1, mc2 = st.columns([1, 1])
    with mc1:
        bono_mep = st.selectbox("Bono", ["AL30", "GD30", "AL29", "GD29", "AL35", "GD35"],
                                key="bono_mep")
        bono_ars_t = bono_mep
        bono_usd_t = bono_mep + "D"

        p_ars_live = bond_prices.get(bono_ars_t)
        p_usd_live = bond_prices.get(bono_usd_t)

        usar_live = st.checkbox("Usar precios de mercado (live)", value=bool(p_ars_live and p_usd_live), key="live_mep")

    with mc2:
        if usar_live and p_ars_live:
            precio_ars = st.number_input(f"Precio {bono_ars_t} en ARS", value=float(p_ars_live),
                                         format="%.4f", step=0.01, key="p_ars_mep")
        else:
            precio_ars = st.number_input(f"Precio {bono_ars_t} en ARS", value=0.0,
                                         format="%.4f", step=0.01, key="p_ars_mep_m")

        if usar_live and p_usd_live:
            precio_usd = st.number_input(f"Precio {bono_usd_t} en USD", value=float(p_usd_live),
                                          format="%.4f", step=0.0001, key="p_usd_mep")
        else:
            precio_usd = st.number_input(f"Precio {bono_usd_t} en USD", value=0.0,
                                          format="%.4f", step=0.0001, key="p_usd_mep_m")

    monto_ars = st.number_input("Monto a invertir (ARS $)", value=1_000_000.0,
                                 min_value=1.0, step=10000.0, format="%.2f", key="monto_mep")

    if precio_ars > 0 and precio_usd > 0:
        # Con costos:
        # Compra en ARS: precio_ars × (1 + com_total) = costo por unidad
        # Venta en USD: precio_usd × (1 - com_total) = cobro por unidad
        costo_por_lote_ars = precio_ars * (1 + com_total)  # ARS por cada 1 VN de bono
        cobro_por_lote_usd = precio_usd * (1 - com_total)  # USD por cada 1 VN

        tc_con_costos = costo_por_lote_ars / cobro_por_lote_usd  # ARS/USD efectivo
        tc_sin_costos = precio_ars / precio_usd  # raw

        # Cantidad de bonos a comprar (en lotes de VN 1)
        lotes = monto_ars / costo_por_lote_ars
        usd_obtenidos = lotes * cobro_por_lote_usd

        # Comisiones en ARS
        com_ars_pesos = monto_ars * com_total
        com_usd_pesos = usd_obtenidos * com_total * tc_con_costos

        st.divider()
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("TC MEP bruto (sin costos)", f"${tc_sin_costos:,.2f}", help="precio_ARS / precio_USD")
        r2.metric("TC MEP neto (con costos)", f"${tc_con_costos:,.2f}", delta=f"{(tc_con_costos/tc_sin_costos-1)*100:+.2f}%")
        r3.metric("USD obtenidos", f"U$S {usd_obtenidos:,.2f}")
        r4.metric("Costo total operación (ARS)", f"${monto_ars * com_total:,.2f}")

        st.markdown("##### 📋 Detalle de la operación")
        st.markdown(f"""
        | Concepto | Valor |
        |---|---|
        | Monto ARS invertido | **${monto_ars:,.2f}** |
        | Precio compra {bono_ars_t} (ARS) | ${precio_ars:.4f} |
        | Precio venta {bono_usd_t} (USD) | U$S {precio_usd:.4f} |
        | Comisión ALyC + DDMM (efectiva) | {com_total*100:.4f}% por punta |
        | Lotes VN negociados | {lotes:,.2f} |
        | **TC MEP neto** | **${tc_con_costos:,.4f}** |
        | **USD obtenidos** | **U$S {usd_obtenidos:,.4f}** |
        """)
    else:
        st.info("Ingresá los precios del bono para calcular el TC MEP.")

# ─────────────────────────────────────────────────────────────────────────────
with tab_ccl:
    st.markdown("##### Compra de USD CCL (Contado con Liquidación)")
    st.caption("Proceso: comprar bono en ARS → vender bono en USD (cuenta exterior / cable)")

    cc1, cc2 = st.columns(2)
    with cc1:
        bono_ccl = st.selectbox("Bono", ["AL30", "GD30", "AL29", "GD29"], key="bono_ccl")
        bono_ccl_ars = bono_ccl
        bono_ccl_usd = bono_ccl + "C"  # ticker con C = cable

        p_ars_ccl_live = bond_prices.get(bono_ccl_ars)
        p_usd_ccl_live = bond_prices.get(bono_ccl_usd)
        usar_live_ccl = st.checkbox("Usar precios live", value=bool(p_ars_ccl_live and p_usd_ccl_live), key="live_ccl")

    with cc2:
        p_ccl_ars = st.number_input(f"Precio {bono_ccl_ars} ARS", value=float(p_ars_ccl_live or 0.0),
                                     format="%.4f", key="p_ccl_ars")
        p_ccl_usd = st.number_input(f"Precio {bono_ccl_usd} USD", value=float(p_usd_ccl_live or 0.0),
                                     format="%.4f", key="p_ccl_usd")

    monto_ccl = st.number_input("Monto ARS a invertir", value=1_000_000.0, step=10000.0,
                                 format="%.2f", key="monto_ccl")

    if p_ccl_ars > 0 and p_ccl_usd > 0:
        tc_ccl_bruto = p_ccl_ars / p_ccl_usd
        costo_ars_u = p_ccl_ars * (1 + com_total)
        cobro_usd_u = p_ccl_usd * (1 - com_total)
        tc_ccl_neto = costo_ars_u / cobro_usd_u
        lotes_ccl = monto_ccl / costo_ars_u
        usd_ccl = lotes_ccl * cobro_usd_u

        r1, r2, r3 = st.columns(3)
        r1.metric("TC CCL bruto", f"${tc_ccl_bruto:,.2f}")
        r2.metric("TC CCL neto", f"${tc_ccl_neto:,.2f}")
        r3.metric("USD obtenidos (cable)", f"U$S {usd_ccl:,.2f}")
    else:
        st.info("Ingresá los precios para calcular el TC CCL.")

# ─────────────────────────────────────────────────────────────────────────────
with tab_canje:
    st.markdown("##### Canje de Especie (AL30 → AL30D)")
    st.caption("Comprar bono en ARS → canjear a especie USD → vender en USD")

    ca1, ca2 = st.columns(2)
    with ca1:
        p_canje_ars = st.number_input("Precio AL30 en ARS", value=float(bond_prices.get("AL30") or 0.0),
                                       format="%.4f", key="p_ca_ars")
        p_canje_usd = st.number_input("Precio AL30D en USD (post-canje)", value=float(bond_prices.get("AL30D") or 0.0),
                                       format="%.4f", key="p_ca_usd")
    with ca2:
        monto_canje = st.number_input("Monto ARS", value=1_000_000.0, step=10000.0,
                                      format="%.2f", key="monto_canje")
        ratio_canje = st.number_input("Ratio canje (AL30/AL30D)", value=1.0, step=0.001,
                                       format="%.4f", help="Generalmente 1:1 para AL30")

    if p_canje_ars > 0 and p_canje_usd > 0:
        lotes_canje = monto_canje / (p_canje_ars * (1 + com_total))
        lotes_d = lotes_canje * ratio_canje
        usd_canje = lotes_d * p_canje_usd * (1 - com_total)
        tc_canje = monto_canje / usd_canje

        c1, c2, c3 = st.columns(3)
        c1.metric("Lotes AL30D obtenidos", f"{lotes_d:,.4f}")
        c2.metric("USD obtenidos", f"U$S {usd_canje:,.4f}")
        c3.metric("TC implícito canje", f"${tc_canje:,.2f}")
    else:
        st.info("Ingresá los precios para calcular el canje.")
