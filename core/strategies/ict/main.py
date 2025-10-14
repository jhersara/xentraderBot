# main.py
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from ict_lord import StrategyICTContinuous

# ================================
# CONFIGURACIÓN DE EJECUCIÓN
# ================================
symbol = "EURUSDm"
timeframe = mt5.TIMEFRAME_M1  # Puedes cambiar el timeframe según necesites
decimal = 0.01
swap = -0.5
tamcontrato = 100
capital_inicial = 100
velas_necesarias = 1000  # Número de velas históricas a descargar

# ================================
# INICIALIZAR MT5
# ================================
print("🔌 Conectando con MetaTrader 5...")

if not mt5.initialize():
    print("❌ Error al inicializar MT5:", mt5.last_error())
    quit()

# Verificar si el símbolo está disponible
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"❌ Símbolo {symbol} no encontrado")
    mt5.shutdown()
    quit()

if not symbol_info.visible:
    print(f"⚠️ Símbolo {symbol} no está visible, intentando activar...")
    if not mt5.symbol_select(symbol, True):
        print(f"❌ No se pudo activar el símbolo {symbol}")
        mt5.shutdown()
        quit()

# ================================
# OBTENER DATOS EN TIEMPO REAL
# ================================
print("📊 Descargando datos históricos desde MT5...")

# Calcular fecha de inicio (desde hace X velas)
utc_from = datetime.now() - timedelta(days=30)  # Descargar datos de los últimos 30 días

# Descargar datos históricos
rates = mt5.copy_rates_from(symbol, timeframe, utc_from, velas_necesarias)

if rates is None:
    print("❌ Error al descargar datos históricos")
    mt5.shutdown()
    quit()

# Convertir a DataFrame
data = pd.DataFrame(rates)
data['time'] = pd.to_datetime(data['time'], unit='s')
data.set_index('time', inplace=True)

# Renombrar columnas para coincidir con tu estrategia
data.rename(columns={
    'open': 'open',
    'high': 'high', 
    'low': 'low',
    'close': 'close',
    'tick_volume': 'volume',
    'spread': 'spread'
}, inplace=True)

# Asegurar que tenemos las columnas necesarias
required_columns = ['open', 'high', 'low', 'close', 'spread']
for col in required_columns:
    if col not in data.columns:
        print(f"❌ Columna {col} no encontrada en los datos")
        mt5.shutdown()
        quit()

print(f"✅ Datos descargados: {len(data)} velas del {data.index[0]} al {data.index[-1]}")

# ================================
# INICIALIZAR ESTRATEGIA
# ================================
print("⚙️ Iniciando estrategia ICT Continuous...")

strategy = StrategyICTContinuous(
    data=data,
    symbol=symbol,
    decimal=decimal,
    swap=swap,
    tamcontrato=tamcontrato,
    velas_15M=9,
    velas_1M=16,
    ratio=5,
    risk=0.01,
    initial_cash=capital_inicial,
    max_operaciones_abiertas=3,
    distancia_minima_entre_operaciones=5
)

# ================================
# EJECUTAR BACKTEST
# ================================
operations = strategy.run()

# ================================
# RESULTADOS
# ================================
results = strategy.get_results()

print("\n===== 📊 RESULTADOS FINALES =====")
for k, v in results.items():
    if isinstance(v, float):
        print(f"{k}: {v:,.2f}")
    else:
        print(f"{k}: {v}")

# ================================
# GRAFICAR EVOLUCIÓN DEL CAPITAL
# ================================
strategy.generar_grafica_evolucion("evolucion_cuenta_continua.png")

# ================================
# CERRAR CONEXIÓN MT5
# ================================
mt5.shutdown()
print("\n✅ Ejecución finalizada con éxito.")