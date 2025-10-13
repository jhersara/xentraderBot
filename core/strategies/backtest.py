from ict_money import StrategyICT
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import argparse
import time

def inicializar_mt5():
    """Inicializa la conexión con MetaTrader 5"""
    if not mt5.initialize():
        print("Error al inicializar MT5")
        print("Asegúrate de que MetaTrader 5 esté abierto y conectado")
        return False
    
    # Verificar que MT5 está conectado
    if not mt5.terminal_info():
        print("MT5 no está conectado al servidor")
        return False
        
    print("Conexión con MT5 establecida correctamente")
    return True

def verificar_y_seleccionar_simbolo(symbol):
    """Verifica si el símbolo existe y lo selecciona en Market Watch"""
    print(f"Verificando símbolo: {symbol}")
    
    # Primero intentar obtener información del símbolo
    symbol_info = mt5.symbol_info(symbol)
    
    if symbol_info is None:
        print(f"El símbolo {symbol} no se encuentra en MT5")
        return False
    
    # Verificar si el símbolo está visible en Market Watch
    if not symbol_info.visible:
        print(f"El símbolo {symbol} no está en Market Watch. Intentando agregarlo...")
        if not mt5.symbol_select(symbol, True):
            print(f"No se pudo agregar {symbol} a Market Watch")
            return False
        print(f"Símbolo {symbol} agregado a Market Watch exitosamente")
    else:
        print(f"Símbolo {symbol} encontrado en Market Watch")
    
    return True

def listar_simbolos_disponibles():
    """Lista todos los símbolos disponibles en MT5"""
    print("Buscando símbolos disponibles...")
    symbols = mt5.symbols_get()
    
    if not symbols:
        print("No se pudieron obtener los símbolos")
        return []
    
    # Filtrar símbolos populares que contengan "EUR"
    eur_symbols = [s.name for s in symbols if "EUR" in s.name and "USD" in s.name]
    popular_symbols = [s.name for s in symbols if any(x in s.name for x in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"])]
    
    print("Símbolos EUR/USD disponibles:")
    for symbol in eur_symbols[:10]:  # Mostrar solo los primeros 10
        print(f"  - {symbol}")
    
    print("\nSímbolos populares disponibles:")
    for symbol in popular_symbols[:10]:
        print(f"  - {symbol}")
    
    return eur_symbols + popular_symbols

def obtener_datos_alternativo(symbol, timeframe, start_date, end_date):
    """Método alternativo para obtener datos si copy_rates_range falla"""
    print("Intentando método alternativo para obtener datos...")
    
    # Calcular cuántas velas necesitamos (aproximadamente)
    days_diff = (end_date - start_date).days
    # En M1, hay aproximadamente 1440 velas por día
    total_velas_necesarias = days_diff * 1440
    
    # Usar copy_rates_from_pos en lugar de copy_rates_range
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, total_velas_necesarias)
    
    if rates is None:
        print("El método alternativo también falló")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    # Filtrar por el rango de fechas requerido
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    return df

def obtener_datos_por_partes(symbol, timeframe, start_date, end_date):
    """Obtiene datos por partes si el rango es muy grande"""
    print("Descargando datos por partes...")
    
    # Dividir el rango en partes de 30 días
    current_start = start_date
    all_data = []
    
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=30), end_date)
        
        print(f"Descargando desde {current_start.date()} hasta {current_end.date()}...")
        
        start_timestamp = int(current_start.timestamp())
        end_timestamp = int(current_end.timestamp())
        
        rates = mt5.copy_rates_range(symbol, timeframe, start_timestamp, end_timestamp)
        
        if rates is not None and len(rates) > 0:
            df_part = pd.DataFrame(rates)
            df_part['time'] = pd.to_datetime(df_part['time'], unit='s')
            df_part.set_index('time', inplace=True)
            all_data.append(df_part)
            print(f"  - {len(rates)} velas descargadas")
        else:
            print(f"  - No se pudieron obtener datos para este período")
        
        current_start = current_end + timedelta(days=1)
        
        # Pequeña pausa para no sobrecargar el servidor
        time.sleep(0.1)
    
    if not all_data:
        return None
    
    # Combinar todos los datos
    final_df = pd.concat(all_data)
    final_df = final_df[~final_df.index.duplicated(keep='first')]
    final_df = final_df.sort_index()
    
    return final_df

def obtener_datos_rango(symbol, timeframe, start_date, end_date):
    """Obtiene datos históricos de MT5 en un rango de fechas"""
    print(f"Solicitando datos desde {start_date} hasta {end_date}")
    
    # Método 1: copy_rates_range directo
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    rates = mt5.copy_rates_range(symbol, timeframe, start_timestamp, end_timestamp)
    
    if rates is not None and len(rates) > 0:
        print(f"Método 1 exitoso: {len(rates)} velas obtenidas")
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df
    
    print("Método 1 falló, intentando método alternativo...")
    
    # Método 2: copy_rates_from_pos
    df = obtener_datos_alternativo(symbol, timeframe, start_date, end_date)
    if df is not None and len(df) > 0:
        print(f"Método 2 exitoso: {len(df)} velas obtenidas")
        return df
    
    print("Método 2 falló, intentando descarga por partes...")
    
    # Método 3: Descarga por partes
    df = obtener_datos_por_partes(symbol, timeframe, start_date, end_date)
    if df is not None and len(df) > 0:
        print(f"Método 3 exitoso: {len(df)} velas obtenidas")
        return df
    
    print("Todos los métodos fallaron para obtener datos")
    return None

def encontrar_simbolo_eurusd_alternativo():
    """Busca un símbolo EURUSD alternativo si EURUSDm no funciona"""
    symbols = mt5.symbols_get()
    
    if not symbols:
        return None
    
    # Buscar variantes de EURUSD
    posibles_simbolos = [
        "EURUSD",
        "EURUSD.",
        "EURUSDm",
        "EURUSD-",
        "EURUSD_",
        "EURUSDq",
        "EURUSDp"
    ]
    
    for symbol in posibles_simbolos:
        for s in symbols:
            if s.name.upper() == symbol.upper():
                print(f"Encontrado símbolo alternativo: {s.name}")
                return s.name
    
    # Si no encuentra exacto, buscar que contenga EURUSD
    for s in symbols:
        if "EURUSD" in s.name.upper():
            print(f"Encontrado símbolo similar: {s.name}")
            return s.name
    
    return None

def ejecutar_backtest():
    """Ejecuta el backtesting con parámetros configurables"""
    parser = argparse.ArgumentParser(description='Backtesting Estrategia ICT')
    parser.add_argument('--symbol', type=str, default='EURUSDm', help='Símbolo a operar')
    parser.add_argument('--capital', type=float, default=10000, help='Capital inicial')
    parser.add_argument('--risk', type=float, default=0.01, help='Riesgo por operación (0.01 = 1%)')
    parser.add_argument('--ratio', type=float, default=2, help='Ratio TP/SL')
    parser.add_argument('--meses', type=int, default=3, help='Meses de backtesting')  # Reducido por defecto
    
    args = parser.parse_args()
    
    # Configuración
    SYMBOL = args.symbol
    # CAPITAL_INICIAL = args.capital
    CAPITAL_INICIAL = 10
    RISK = args.risk
    RATIO = args.ratio
    MESES_BACKTEST = args.meses
    
    # Calcular fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=MESES_BACKTEST * 30)
    
    print("=" * 60)
    print("BACKTESTING ESTRATEGIA ICT")
    print("=" * 60)
    print(f"Símbolo: {SYMBOL}")
    print(f"Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    print(f"Duración: {MESES_BACKTEST} meses")
    print(f"Capital inicial: ${CAPITAL_INICIAL:,.2f}")
    print(f"Riesgo por operación: {RISK * 100}%")
    print(f"Ratio TP/SL: {RATIO}:1")
    print("=" * 60)
    
    # Inicializar MT5
    if not inicializar_mt5():
        print("No se pudo inicializar MT5. Verifica:")
        print("1. Que MetaTrader 5 esté instalado y ejecutándose")
        print("2. Que tengas una cuenta demo o real configurada")
        print("3. Que estés conectado a internet")
        return
    
    try:
        # Verificar símbolo
        symbol_a_usar = SYMBOL
        if not verificar_y_seleccionar_simbolo(symbol_a_usar):
            print(f"\nEl símbolo {symbol_a_usar} no está disponible.")
            print("Buscando símbolo alternativo...")
            
            symbol_alternativo = encontrar_simbolo_eurusd_alternativo()
            if symbol_alternativo:
                print(f"Usando símbolo alternativo: {symbol_alternativo}")
                symbol_a_usar = symbol_alternativo
            else:
                print("No se encontró un símbolo alternativo adecuado.")
                listar_simbolos_disponibles()
                return
        
        # Obtener datos
        print("\nDescargando datos históricos...")
        data = obtener_datos_rango(symbol_a_usar, mt5.TIMEFRAME_M1, start_date, end_date)
        
        if data is None or len(data) == 0:
            print("No se pudieron obtener datos históricos.")
            print("Intentando con un período más corto...")
            
            # Intentar con solo 1 mes
            start_date_short = end_date - timedelta(days=30)
            data = obtener_datos_rango(symbol_a_usar, mt5.TIMEFRAME_M1, start_date_short, end_date)
            
            if data is None or len(data) == 0:
                print("No se pudieron obtener datos incluso con período corto.")
                print("Posibles soluciones:")
                print("1. Verifica que el símbolo exista en tu plataforma MT5")
                print("2. Asegúrate de tener datos históricos para el período")
                print("3. Prueba con un símbolo diferente como 'EURUSD'")
                return
        
        print(f"✓ Datos descargados exitosamente: {len(data)} velas M1")
        print(f"✓ Rango de datos: {data.index[0]} a {data.index[-1]}")
        
        # Verificar que tenemos las columnas necesarias
        required_columns = ['open', 'high', 'low', 'close', 'spread']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"✗ Faltan columnas en los datos: {missing_columns}")
            return
        
        # Asegurarse de que tenemos datos de spread (si no, crear unos ficticios)
        if 'spread' not in data.columns or data['spread'].isnull().all():
            print("Nota: No se encontraron datos de spread, usando valores por defecto")
            data['spread'] = 10  # Spread típico para EURUSD
        
        # Parámetros de la estrategia
        PARAMS = {
            'symbol': symbol_a_usar,
            'decimal': 0.0001,
            'swap': 0,
            'tamcontrato': 100000,
            'velas_15M': 3,
            'velas_1M': 30,
            'ratio': RATIO,
            'risk': RISK,
            'initial_cash': CAPITAL_INICIAL
        }
        
        # Crear y ejecutar estrategia
        print("Ejecutando backtesting...")
        estrategia = StrategyICT(data, **PARAMS)
        operaciones = estrategia.run()
        
        # Mostrar resultados detallados
        resultados = estrategia.get_results()
        
        print("\n" + "="*60)
        print("RESULTADOS BACKTESTING - ESTRATEGIA ICT")
        print("="*60)
        print(f"Par: {symbol_a_usar}")
        print(f"Período: {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}")
        print(f"Duración: {(data.index[-1] - data.index[0]).days} días")
        print("-" * 60)
        print(f"Capital inicial:    ${resultados['capital_inicial']:>12,.2f}")
        print(f"Capital final:      ${resultados['capital_final']:>12,.2f}")
        print(f"Profit/Total:       ${resultados['profit_total']:>12,.2f} ({resultados['profit_percent']:>6.2f}%)")
        print("-" * 60)
        print(f"Total operaciones:  {resultados['total_operaciones']:>12}")
        print(f"Operaciones ganadas:{resultados['operaciones_ganadas']:>12}")
        print(f"Operaciones perdidas:{resultados['operaciones_perdidas']:>11}")
        print(f"Porcentaje de acierto: {resultados['porcentaje_ganadas']:>8.2f}%")
        print("=" * 60)
        
        # Estadísticas adicionales
        if operaciones:
            resultados_positivos = [op['Resultado'] for op in operaciones if op['Resultado'] > 0]
            resultados_negativos = [op['Resultado'] for op in operaciones if op['Resultado'] <= 0]
            
            avg_ganancia = sum(resultados_positivos) / len(resultados_positivos) if resultados_positivos else 0
            avg_perdida = sum(resultados_negativos) / len(resultados_negativos) if resultados_negativos else 0
            
            profit_factor = 0
            if resultados_negativos and sum(resultados_negativos) != 0:
                profit_factor = abs(sum(resultados_positivos) / sum(resultados_negativos))
            
            print(f"Ganancia promedio:  ${avg_ganancia:>12,.2f}")
            print(f"Pérdida promedio:   ${avg_perdida:>12,.2f}")
            ratio_ganancia_perdida = avg_ganancia/abs(avg_perdida) if avg_perdida != 0 else 0
            print(f"Ratio ganancia/pérdida: {ratio_ganancia_perdida:>8.2f}")
            print(f"Profit Factor:      {profit_factor:>12.2f}")
            
            # Mostrar últimas operaciones
            if len(operaciones) > 0:
                print(f"\nÚltimas 5 operaciones:")
                for op in operaciones[-5:]:
                    resultado = op['Resultado']
                    color = "\033[92m" if resultado > 0 else "\033[91m"
                    reset = "\033[0m"
                    tipo_str = "SHORT" if op['Tipo'] == 'short' else "LONG "
                    fecha_entrada = op['Fecha de entrada'].strftime('%Y-%m-%d %H:%M')
                    precio_entrada = op['Precio de entrada']
                    precio_salida = op.get('Precio salida', 'N/A')
                    
                    print(f"{fecha_entrada} | {tipo_str} | Entrada: {precio_entrada:.5f} | "
                          f"Salida: {precio_salida} | Resultado: {color}${resultado:,.2f}{reset}")
        
        else:
            print("\nNo se ejecutaron operaciones durante el período de backtesting")
            print("Posibles razones:")
            print("1. No se cumplieron las condiciones de la estrategia")
            print("2. El período de backtesting es muy corto")
            print("3. Los parámetros de la estrategia son muy estrictos")
            
    except Exception as e:
        print(f"Error durante el backtesting: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        mt5.shutdown()
        print("\nConexión con MT5 cerrada")

if __name__ == "__main__":
    ejecutar_backtest()