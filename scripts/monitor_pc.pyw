import os, sqlite3, json, time, psutil, pynvml
from datetime import datetime, timedelta

# --- MANEJO DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'energia.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'settings.json')

def cargar_configuracion():
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            return config['pc_stats']['watts_promedio']
    except:
        return 250

def inicializar_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla principal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consumo_pc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            segundos_uso INTEGER,
            kwh_consumidos REAL,
            carga_cpu_promedio REAL
        )
    ''')
    
    # Parche automático para la columna de GPU
    try:
        cursor.execute("ALTER TABLE consumo_pc ADD COLUMN carga_gpu_promedio REAL")
    except:
        pass # La columna ya existe
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aparato TEXT,
            watts INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def registrar_sesion(inicio, fin, watts, lista_cargas):
    duracion_segundos = int((fin - inicio).total_seconds())
    if duracion_segundos <= 0: return 
    
    cpu_prom = sum(c[0] for c in lista_cargas) / len(lista_cargas) if lista_cargas else 2.0
    gpu_prom = sum(c[1] for c in lista_cargas) / len(lista_cargas) if lista_cargas else 0.0
    
    # FÓRMULA DE PESOS REALES (24% Base + 26% CPU + 50% GPU)
    factor_ajuste = 0.24 + (0.26 * (cpu_prom / 100)) + (0.50 * (gpu_prom / 100))
    consumo_kwh = (watts * factor_ajuste * (duracion_segundos / 3600)) / 1000

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO consumo_pc (fecha, hora_inicio, hora_fin, segundos_uso, kwh_consumidos, carga_cpu_promedio, carga_gpu_promedio)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (inicio.strftime('%Y-%m-%d'), 
          inicio.strftime('%H:%M:%S'), 
          fin.strftime('%H:%M:%S'), 
          duracion_segundos, 
          round(consumo_kwh, 4),
          round(cpu_prom, 2),
          round(gpu_prom, 2)))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_db()
    try:
        pynvml.nvmlInit()
        tiene_gpu = True
    except:
        tiene_gpu = False

    # --- SINCRONIZACIÓN INTELIGENTE (UPTIME) ---
    try:
        conn = sqlite3.connect(DB_PATH)
        ultimo = conn.execute("SELECT fecha, hora_fin FROM consumo_pc ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        ahora = datetime.now()
        watts_pc = cargar_configuracion()
        if ultimo:
            ultimo_dt = datetime.strptime(f"{ultimo[0]} {ultimo[1]}", '%Y-%m-%d %H:%M:%S')
            segundos_desde_ultimo = (ahora - ultimo_dt).total_seconds()
            if segundos_desde_ultimo > 60 and ultimo_dt.timestamp() > psutil.boot_time():
                tiempo_rec = min(segundos_desde_ultimo, ahora.timestamp() - psutil.boot_time())
                registrar_sesion(ahora - timedelta(seconds=tiempo_rec), ahora, watts_pc, [(2.0, 0.0)])
            else:
                registrar_sesion(ahora - timedelta(seconds=1), ahora, watts_pc, [(2.0, 0.0)])
    except:
        pass

    cargas_segundo = []
    inicio_sesion = datetime.now()
    
    try:
        while True:
            watts_pc = cargar_configuracion()
            c_cpu = psutil.cpu_percent()
            c_gpu = 0
            if tiene_gpu:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    c_gpu = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                except: pass
            
            cargas_segundo.append((c_cpu, c_gpu))
            ahora = datetime.now()
            if (ahora - inicio_sesion).total_seconds() >= 900:
                registrar_sesion(inicio_sesion, ahora, watts_pc, cargas_segundo)
                inicio_sesion = ahora
                cargas_segundo = []
                
            time.sleep(10) # Optimización de RAM/CPU
    except Exception as e:
        fin_s = datetime.now()
        if len(cargas_segundo) > 0:
            registrar_sesion(inicio_sesion, fin_s, cargar_configuracion(), cargas_segundo)