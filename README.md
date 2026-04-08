# Portfolio Investment — Streamlit App

Sistema de Cálculo Financiero para mercados de capitales argentinos.
Conversión de Herramientas-4 (HTML/JS) a Python + Streamlit.

---

## Cómo instalar y ejecutar (paso a paso)

### Requisitos previos
- Tener **Python 3.10 o superior** instalado.  
  Verificá con: `python --version`

### 1. Descomprimí el archivo ZIP
Descomprimí `portfolio_investment.zip` en la carpeta que quieras.

### 2. Abrí una terminal en esa carpeta
En Windows: click derecho → "Abrir terminal" o "Abrir en PowerShell"  
En Mac/Linux: `cd /ruta/a/portfolio_investment`

### 3. Instalá las dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutá la app
```bash
streamlit run app.py
```

Se va a abrir automáticamente el navegador en `http://localhost:8501`.

---

## Estructura de archivos

```
portfolio_investment/
├── app.py                    ← Punto de entrada (Resumen de mercado)
├── utils.py                  ← Funciones compartidas (APIs, math financiero)
├── requirements.txt          ← Dependencias Python
├── README.md                 ← Este archivo
└── pages/
    ├── 1_💸_TC_MEP_CCL.py    ← Calculadora TC / MEP / CCL
    ├── 2_⬡_Cauciones.py      ← Cauciones Bursátiles
    ├── 3_📄_Cheques.py        ← Descuento de Cheques (CPD)
    ├── 4_🔧_Op_Neta.py        ← Operación Neta (costos ALyC)
    ├── 5_◆_LECAP_BONCAP.py   ← LECAP / BONCAP (pesos)
    ├── 6_🌐_Bonos_USD.py      ← Bonos Soberanos USD (TIR Newton-Raphson)
    ├── 7_📈_Bonos_CER.py      ← Bonos CER (TIR Real)
    ├── 8_💵_Dolar_Linked.py   ← Dólar Linked (devaluación implícita)
    └── 9_⇄_Arbitraje.py      ← Arbitraje GD30/AL30 + Bollinger Bands
```

---

## Fuentes de datos

| Dato | API |
|---|---|
| Precios bonos soberanos | `data912.com/live/arg_bonds` |
| LECAP / BONCAP | `data912.com/live/arg_notes` |
| FX (oficial, MEP, CCL, blue) | `dolarapi.com/v1/dolares` |
| Índice CER | `api.argentinadatos.com/v1/finanzas/indices/cer` |

---

## Notas importantes

- **Flujos de fondos de bonos soberanos**: los schedules están hardcodeados basados en los prospectos del canje 2020. Verificar siempre contra [rendimientos.co](https://rendimientos.co).
- Los precios se actualizan cada 25–30 segundos automáticamente (caché de Streamlit).
- El historial del Arbitraje persiste solo durante la sesión activa. Para historial permanente, cargá un CSV.

---

## Troubleshooting

**"No module named streamlit"**  
→ Corré `pip install -r requirements.txt` de nuevo.

**La app abre pero no muestra precios**  
→ Verificá tu conexión a internet. Las APIs son públicas y gratuitas.

**Error en Windows con emojis en nombres de archivo**  
→ Usá Python 3.10+ y Streamlit 1.35+. Si persiste, renombrá las páginas sin emojis (ej: `1_TC.py`).
