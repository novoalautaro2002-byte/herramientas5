"""
pages/4_🔧_Op_Neta.py
Calculadora de Operación Neta: precio final con todos los gastos incluidos.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import apply_style, page_header

st.set_page_config(page_title="Operación Neta", page_icon="🔧", layout="wide")
apply_style()
page_header("Operación Neta", subtitle="Calculadora · Precio con Aranceles y Costos", icon="◈")

st.caption("Calculá el precio de compra o venta con todos los costos incluidos: comisiones, DDMM, IVA, derechos de bolsa.")

tab_compra, tab_venta = st.tabs(["📥 Compra (¿cuánto pago en total?)", "📤 Venta (¿cuánto recibo neto?)"])

def calcular_costos(precio_neto: float, cantidad: float, com_pct: float, iva_pct: float,
                    ddmm_pct: float, der_bolsa_pct: float, modo: str):
    """
    precio_neto: precio limpio del activo (sin accrued interest aquí, ese se suma aparte)
    cantidad: número de unidades / nominales
    modo: "compra" o "venta"
    """
    monto_base = precio_neto * cantidad
    com_bruta   = monto_base * com_pct / 100
    iva_monto   = com_bruta * iva_pct / 100
    com_total   = com_bruta + iva_monto
    ddmm_monto  = monto_base * ddmm_pct / 100
    der_monto   = monto_base * der_bolsa_pct / 100

    total_cargos = com_total + ddmm_monto + der_monto

    if modo == "compra":
        monto_final = monto_base + total_cargos
    else:
        monto_final = monto_base - total_cargos

    precio_efectivo = monto_final / cantidad if cantidad > 0 else 0

    return {
        "monto_base": monto_base,
        "comision_bruta": com_bruta,
        "iva_comision": iva_monto,
        "comision_total": com_total,
        "ddmm": ddmm_monto,
        "derechos_bolsa": der_monto,
        "total_cargos": total_cargos,
        "monto_final": monto_final,
        "precio_efectivo": precio_efectivo,
    }


# ─── Parámetros comunes ────────────────────────────────────────────────────────
with st.expander("⚙️ Aranceles y comisiones", expanded=True):
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        com_pct = st.number_input("Comisión ALyC (%)", value=0.50, min_value=0.0, step=0.05, format="%.4f")
    with pc2:
        iva_pct = st.number_input("IVA sobre comisión (%)", value=21.0, min_value=0.0, step=1.0)
    with pc3:
        ddmm_pct = st.number_input("DDMM (%)", value=0.0100, min_value=0.0, step=0.001, format="%.4f",
                                    help="Derechos de Mercado — 0.0100% por punta (BYMA)")
    with pc4:
        der_bolsa_pct = st.number_input("Der. Bolsa (%)", value=0.0, min_value=0.0, step=0.001, format="%.4f",
                                         help="Derecho de bolsa (si aplica)")

# ─── Compra ───────────────────────────────────────────────────────────────────
with tab_compra:
    st.markdown("#### Calculá el costo total de compra")

    b1, b2 = st.columns(2)
    with b1:
        precio_c = st.number_input("Precio unitario del activo", value=100.0, step=0.01, format="%.4f", key="pc")
        cant_c = st.number_input("Cantidad / Nominales", value=10000.0, step=100.0, format="%.2f", key="qc")
        ic_c = st.number_input("Interés corrido (si aplica, por unidad)", value=0.0,
                                step=0.001, format="%.4f", key="ic_c",
                                help="Para bonos: interés devengado desde el último cupón")
        moneda = st.selectbox("Moneda", ["ARS ($)", "USD (U$S)"], key="mon_c")

    with b2:
        if precio_c > 0 and cant_c > 0:
            precio_sucio = precio_c + ic_c
            res = calcular_costos(precio_sucio, cant_c, com_pct, iva_pct, ddmm_pct, der_bolsa_pct, "compra")
            sym = "$" if "ARS" in moneda else "U$S"

            st.markdown("#### Resultado")
            r1, r2 = st.columns(2)
            r1.metric("Monto base (precio limpio)", f"{sym}{res['monto_base']:,.2f}")
            r2.metric("Total cargos", f"{sym}{res['total_cargos']:,.2f}",
                      delta=f"{res['total_cargos']/res['monto_base']*100:.3f}%")
            st.metric("**TOTAL A PAGAR**", f"{sym}{res['monto_final']:,.4f}")
            st.metric("Precio efectivo por unidad", f"{sym}{res['precio_efectivo']:,.4f}")

            st.divider()
            st.markdown(f"""
            | Concepto | {sym} |
            |---|---|
            | Precio unitario | {sym}{precio_c:,.4f} |
            | Interés corrido | {sym}{ic_c:,.4f} |
            | Precio sucio unitario | {sym}{precio_sucio:,.4f} |
            | Monto base ({cant_c:,.0f} × {sym}{precio_sucio:,.4f}) | {sym}{res['monto_base']:,.4f} |
            | Comisión ALyC ({com_pct:.4f}%) | {sym}{res['comision_bruta']:,.4f} |
            | IVA sobre comisión ({iva_pct:.0f}%) | {sym}{res['iva_comision']:,.4f} |
            | DDMM ({ddmm_pct:.4f}%) | {sym}{res['ddmm']:,.4f} |
            | Derechos de bolsa ({der_bolsa_pct:.4f}%) | {sym}{res['derechos_bolsa']:,.4f} |
            | **Total cargos** | **{sym}{res['total_cargos']:,.4f}** |
            | **TOTAL A PAGAR** | **{sym}{res['monto_final']:,.4f}** |
            """)

# ─── Venta ────────────────────────────────────────────────────────────────────
with tab_venta:
    st.markdown("#### Calculá el neto a recibir por venta")

    v1, v2 = st.columns(2)
    with v1:
        precio_v = st.number_input("Precio unitario del activo", value=100.0, step=0.01, format="%.4f", key="pv")
        cant_v = st.number_input("Cantidad / Nominales", value=10000.0, step=100.0, format="%.2f", key="qv")
        ic_v = st.number_input("Interés corrido (por unidad)", value=0.0, step=0.001,
                                format="%.4f", key="ic_v")
        moneda_v = st.selectbox("Moneda", ["ARS ($)", "USD (U$S)"], key="mon_v")

    with v2:
        if precio_v > 0 and cant_v > 0:
            precio_sucio_v = precio_v + ic_v
            res_v = calcular_costos(precio_sucio_v, cant_v, com_pct, iva_pct, ddmm_pct, der_bolsa_pct, "venta")
            sym_v = "$" if "ARS" in moneda_v else "U$S"

            st.markdown("#### Resultado")
            r1v, r2v = st.columns(2)
            r1v.metric("Monto bruto operado", f"{sym_v}{res_v['monto_base']:,.2f}")
            r2v.metric("Total cargos descontados", f"{sym_v}{res_v['total_cargos']:,.2f}",
                       delta=f"-{res_v['total_cargos']/res_v['monto_base']*100:.3f}%")
            st.metric("**NETO A RECIBIR**", f"{sym_v}{res_v['monto_final']:,.4f}")
            st.metric("Precio neto por unidad", f"{sym_v}{res_v['precio_efectivo']:,.4f}")

            st.divider()
            st.markdown(f"""
            | Concepto | {sym_v} |
            |---|---|
            | Monto bruto | {sym_v}{res_v['monto_base']:,.4f} |
            | − Comisión + IVA | −{sym_v}{res_v['comision_total']:,.4f} |
            | − DDMM | −{sym_v}{res_v['ddmm']:,.4f} |
            | − Derechos bolsa | −{sym_v}{res_v['derechos_bolsa']:,.4f} |
            | **NETO A RECIBIR** | **{sym_v}{res_v['monto_final']:,.4f}** |
            """)
