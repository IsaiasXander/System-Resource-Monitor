import streamlit as st
import sqlite3, pandas as pd, plotly.express as px, os, json, datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'energia.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.json')

st.set_page_config(page_title="Energy-Logic Dashboard", layout="wide")

def cargar_config():
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

def leer_datos(query):
    if not os.path.exists(DB_PATH): return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
    except:
        df = pd.DataFrame() 
    conn.close()
    return df

# --- INTERFAZ ---
st.title("🖥️ Energy-Logic: Analista Forense")
config = cargar_config()
df = leer_datos("SELECT * FROM consumo_pc")

# --- CRONÓMETRO (UBICACIÓN BARRA LATERAL) ---
if not df.empty:
    try:
        ultimo_reg = df.iloc[-1]
        ultimo_dt = datetime.datetime.strptime(f"{ultimo_reg['fecha']} {ultimo_reg['hora_fin']}", '%Y-%m-%d %H:%M:%S')
        segundos_faltantes = int(900 - (datetime.datetime.now() - ultimo_dt).total_seconds() + 5)

        if segundos_faltantes > 0:
            with st.sidebar:
                st.markdown("### ⏳ Tiempo para el próximo depósito")
                js_timer = f"""
                    <div id="timer" style="color: #00d4ff; font-size: 32px; font-family: sans-serif; font-weight: bold; background: #0e1117; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #30363d;">
                        00:00
                    </div>
                    <script>
                        let timeLeft = {segundos_faltantes};
                        setInterval(() => {{
                            if (timeLeft <= 0) window.parent.location.reload();
                            let mins = Math.floor(timeLeft / 60);
                            let secs = timeLeft % 60;
                            document.getElementById('timer').innerHTML = (mins < 10 ? \"0\" : \"\") + mins + \":\" + (secs < 10 ? \"0\" : \"\") + secs;
                            timeLeft--;
                        }}, 1000);
                    </script>
                """
                components.html(js_timer, height=100)
    except:
        st.sidebar.error("Error de sincronización del reloj")

# --- DASHBOARD PRINCIPAL ---
if df.empty:
    st.info("Esperando datos del Vigilante...")
else:
    total_kwh = df['kwh_consumidos'].sum()
    costo = total_kwh * config['tarifa_electrica']['costo_kwh']
    total_seg = df['segundos_uso'].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Consumido", f"{total_kwh:.4f} kWh")
    m2.metric("Gasto Estimado", f"${costo:.2f} MXN")
    m3.metric("Sesiones", len(df))
    m4.metric("Tiempo Activo", f"{int(total_seg // 3600)}h {int((total_seg % 3600) // 60)}m")

    fig = px.bar(df, x='id', y='kwh_consumidos', title="Consumo por Bloques de 15 min", template="plotly_dark")
    st.plotly_chart(fig, width='stretch')

    # --- DETALLE HISTÓRICO CON FORMATO VISUAL % ---
    st.subheader("📋 Detalle Histórico")
    
    # Creamos una copia para visualización
    df_v = df.copy()
    
    # Aplicamos el formato de porcentaje solo a las columnas de carga
    if 'carga_cpu_promedio' in df_v.columns:
        df_v['CPU %'] = df_v['carga_cpu_promedio'].apply(lambda x: f"{x}%" if pd.notnull(x) else "0%")
    
    if 'carga_gpu_promedio' in df_v.columns:
        df_v['GPU %'] = df_v['carga_gpu_promedio'].apply(lambda x: f"{x}%" if pd.notnull(x) else "0%")
    
    # Seleccionamos las columnas formateadas para la tabla
    cols = [c for c in ['id','fecha','hora_inicio','hora_fin','kwh_consumidos','CPU %','GPU %'] if c in df_v.columns]
    st.dataframe(df_v[cols].sort_values(by='id', ascending=False), width='stretch')

# --- INVENTARIO ---
st.sidebar.divider()
st.sidebar.subheader("🔌 Inventario")
with st.sidebar.form("inv_form", clear_on_submit=True):
    nombre_ap = st.text_input("Aparato")
    watts_ap = st.number_input("Watts", min_value=1, value=100)
    if st.form_submit_button("Registrar"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO inventario (aparato, watts) VALUES (?,?)", (nombre_ap, watts_ap))
        conn.commit(); conn.close(); st.rerun()

df_inv = leer_datos("SELECT * FROM inventario")
if not df_inv.empty:
    st.sidebar.dataframe(df_inv[['aparato', 'watts']], width='stretch')