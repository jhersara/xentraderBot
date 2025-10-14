# backtest_4_years.py
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import time
import os
import sys
from tqdm import tqdm
import talib
import warnings
warnings.filterwarnings('ignore')

# Importar tu estrategia
from ict_lord import StrategyICTContinuous

class FourYearBacktest:
    def __init__(self, symbol='EURUSDm', capital_inicial=100, risk=0.01):
        self.symbol = symbol
        self.capital_inicial = capital_inicial
        self.risk = risk
        self.tamcontrato = 100000
        self.decimal = 0.0001
        
    def inicializar_mt5(self):
        """Inicializa MT5 con manejo de errores mejorado"""
        try:
            if not mt5.initialize():
                print("❌ Error: No se pudo inicializar MT5")
                print("   - Verifica que MT5 esté abierto")
                print("   - Verifica tu conexión a internet")
                return False
            
            # Esperar a que MT5 esté listo
            time.sleep(2)
            
            if not mt5.terminal_info():
                print("❌ Error: MT5 no está conectado al servidor")
                return False
                
            print("✅ Conexión con MT5 establecida")
            return True
            
        except Exception as e:
            print(f"❌ Error crítico inicializando MT5: {e}")
            return False
    
    def encontrar_simbolo_optimo(self):
        """Encuentra el mejor símbolo disponible"""
        simbolos_preferidos = ['EURUSD', 'EURUSDm', 'EURUSD.', 'EURUSD-', 'EURUSD_']
        
        for simbolo in simbolos_preferidos:
            if self.verificar_simbolo(simbolo):
                print(f"✅ Usando símbolo: {simbolo}")
                self.symbol = simbolo
                return True
        
        # Buscar cualquier símbolo que contenga EURUSD
        try:
            todos_simbolos = mt5.symbols_get()
            for simbolo_info in todos_simbolos:
                if 'EURUSD' in simbolo_info.name.upper():
                    print(f"✅ Encontrado símbolo alternativo: {simbolo_info.name}")
                    self.symbol = simbolo_info.name
                    return self.verificar_simbolo(simbolo_info.name)
        except:
            pass
            
        return False
    
    def verificar_simbolo(self, symbol):
        """Verifica si un símbolo está disponible"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return False
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return False
            
            # Verificar que tenemos datos históricos
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
            return rates is not None and len(rates) > 0
            
        except:
            return False
    
    def descargar_datos_por_años(self, años=4):
        """Descarga datos divididos por años para mejor manejo de memoria"""
        print(f"📅 Descargando datos de {años} años...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=años*365)
        
        # Dividir por años
        datos_por_año = {}
        
        for año in range(años):
            año_start = end_date - timedelta(days=(años-año)*365)
            año_end = año_start + timedelta(days=365)
            
            # Ajustar para el primer y último año
            if año == 0:
                año_start = start_date
            if año == años - 1:
                año_end = end_date
            
            print(f"   🗓️  Descargando año {año_start.year}...")
            
            datos_año = self.descargar_rango_fechas(año_start, año_end)
            if datos_año is not None and len(datos_año) > 0:
                datos_por_año[año_start.year] = datos_año
                print(f"      ✅ {len(datos_año)} velas descargadas")
            else:
                print(f"      ❌ No se pudieron obtener datos para {año_start.year}")
        
        # Combinar todos los datos
        if not datos_por_año:
            return None
        
        todos_datos = pd.concat(datos_por_año.values())
        todos_datos = todos_datos[~todos_datos.index.duplicated(keep='first')]
        todos_datos = todos_datos.sort_index()
        
        print(f"✅ Datos combinados: {len(todos_datos)} velas totales")
        return todos_datos
    
    def descargar_rango_fechas(self, start_date, end_date):
        """Descarga datos para un rango de fechas específico"""
        try:
            # Método 1: copy_rates_range
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, start_timestamp, end_timestamp)
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                return df
            
            # Método 2: copy_rates_from_pos (si el anterior falla)
            print("      ⚠️  Método 1 falló, intentando método alternativo...")
            return self.descargar_por_copias(self.symbol, start_date, end_date)
            
        except Exception as e:
            print(f"      ❌ Error descargando rango: {e}")
            return None
    
    def descargar_por_copias(self, symbol, start_date, end_date):
        """Método alternativo para descargar datos"""
        try:
            # Calcular número aproximado de velas necesarias
            dias_totales = (end_date - start_date).days
            velas_aproximadas = dias_totales * 1440  # 1440 velas M1 por día
            
            # Descargar desde la posición 0
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, velas_aproximadas)
            
            if rates is None:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Filtrar por el rango que necesitamos
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            return df if len(df) > 0 else None
            
        except Exception as e:
            print(f"      ❌ Error en método alternativo: {e}")
            return None
    
    def preparar_datos(self, data):
        """Prepara los datos para la estrategia"""
        if data is None or len(data) == 0:
            return None
        
        # Verificar columnas requeridas
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            print(f"❌ Faltan columnas: {missing_cols}")
            return None
        
        # Añadir columnas necesarias si no existen
        if 'spread' not in data.columns:
            data['spread'] = 10  # Valor por defecto
        
        # Calcular ATR si no existe (para la estrategia)
        if 'ATR' not in data.columns:
            try:
                data['ATR'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
                data['slippage'] = data['ATR'] * 0.003
            except:
                data['ATR'] = 0.001
                data['slippage'] = 0.0001
        
        print(f"✅ Datos preparados: {len(data)} velas")
        print(f"   📅 Rango: {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}")
        
        return data
    
    def ejecutar_backtest_completo(self, años=4, ratio=4, velas_15M=16, velas_1M=9):
        """Ejecuta el backtesting completo para 4 años"""
        print("🚀 INICIANDO BACKTESTING DE 4 AÑOS")
        print("=" * 60)
        
        # 1. Inicializar MT5
        if not self.inicializar_mt5():
            return None
        
        try:
            # 2. Encontrar símbolo óptimo
            if not self.encontrar_simbolo_optimo():
                print("❌ No se pudo encontrar un símbolo válido")
                return None
            
            # 3. Descargar datos de 4 años
            data = self.descargar_datos_por_años(años)
            if data is None:
                print("❌ No se pudieron descargar datos históricos")
                return None
            
            # 4. Preparar datos
            data = self.preparar_datos(data)
            if data is None:
                return None
            
            # 5. Configurar parámetros de la estrategia
            params = {
                'data': data,
                'symbol': self.symbol,
                'decimal': self.decimal,
                'swap': 0,
                'tamcontrato': self.tamcontrato,
                'velas_15M': velas_15M,
                'velas_1M': velas_1M,
                'ratio': ratio,
                'risk': self.risk,
                'initial_cash': self.capital_inicial,
                'max_operaciones_abiertas': 3,
                'distancia_minima_entre_operaciones': 5
            }
            
            print("🎯 CONFIGURACIÓN DE ESTRATEGIA:")
            print(f"   - Velas M15: {velas_15M}")
            print(f"   - Velas M1: {velas_1M}")
            print(f"   - Ratio: {ratio}")
            print(f"   - Risk: {self.risk*100}%")
            print(f"   - Capital: ${self.capital_inicial:,.2f}")
            print("=" * 60)
            
            # 6. Ejecutar estrategia con barra de progreso
            print("🔄 Ejecutando estrategia...")
            estrategia = StrategyICTContinuous(**params)
            
            # Ejecutar con barra de progreso
            operaciones = estrategia.run()
            
            # 7. Obtener y mostrar resultados
            resultados = self.analizar_resultados(estrategia, operaciones)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error durante el backtesting: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            mt5.shutdown()
            print("🔌 Conexión MT5 cerrada")
    
    def analizar_resultados(self, estrategia, operaciones):
        """Analiza y muestra los resultados del backtesting"""
        if not operaciones:
            print("❌ No se ejecutaron operaciones")
            return None
        
        resultados = estrategia.get_results()
        
        print("\n" + "=" * 70)
        print("📊 RESULTADOS BACKTESTING - 4 AÑOS")
        print("=" * 70)
        
        # Métricas básicas
        print(f"💰 CAPITAL:")
        print(f"   Inicial:    ${resultados['capital_inicial']:>12,.2f}")
        print(f"   Final:      ${resultados['capital_final']:>12,.2f}")
        print(f"   Profit:     ${resultados['profit_total']:>12,.2f} ({resultados['profit_percent']:>6.2f}%)")
        
        print(f"\n📈 OPERACIONES:")
        print(f"   Totales:    {resultados['total_operaciones']:>12}")
        print(f"   Ganadoras:  {resultados['operaciones_ganadas']:>12}")
        print(f"   Perdedoras: {resultados['operaciones_perdidas']:>11}")
        print(f"   Win Rate:   {resultados['porcentaje_ganadas']:>11.2f}%")
        
        # Métricas avanzadas
        if 'profit_promedio' in resultados:
            print(f"\n🎯 MÉTRICAS AVANZADAS:")
            print(f"   Profit promedio:  ${resultados['profit_promedio']:>10,.2f}")
            print(f"   Pérdida promedio: ${resultados['perdida_promedio']:>10,.2f}")
            print(f"   Ratio G/P:        {resultados['ratio_ganancia_perdida']:>10.2f}")
            print(f"   Máxima ganancia:  ${resultados['maxima_ganancia']:>10,.2f}")
            print(f"   Máxima pérdida:   ${resultados['maxima_perdida']:>10,.2f}")
        
        # Calcular Profit Factor manualmente si no está en resultados
        ganancias_totales = sum([op['Resultado'] for op in operaciones if op['Resultado'] > 0])
        perdidas_totales = abs(sum([op['Resultado'] for op in operaciones if op['Resultado'] < 0]))
        
        profit_factor = ganancias_totales / perdidas_totales if perdidas_totales > 0 else float('inf')
        print(f"   Profit Factor:   {profit_factor:>10.2f}")
        
        # Evolución del capital
        capital_evolution = estrategia.capital_evolution
        if len(capital_evolution) > 1:
            max_capital = max(capital_evolution)
            min_capital = min(capital_evolution)
            max_drawdown = (min_capital - max_capital) / max_capital * 100
            
            print(f"\n📉 EVOLUCIÓN:")
            print(f"   Capital máximo:  ${max_capital:>10,.2f}")
            print(f"   Capital mínimo:  ${min_capital:>10,.2f}")
            print(f"   Max Drawdown:    {max_drawdown:>9.1f}%")
        
        print("=" * 70)
        
        # Generar gráfica
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"backtest_4years_{timestamp}.png"
        estrategia.generar_grafica_evolucion(filename)
        
        return {
            'resultados': resultados,
            'operaciones': operaciones,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown if 'max_drawdown' in locals() else 0
        }

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Backtesting de 4 años - Estrategia ICT')
    parser.add_argument('--symbol', type=str, default='EURUSDm', help='Símbolo a operar')
    parser.add_argument('--capital', type=float, default=100, help='Capital inicial')
    parser.add_argument('--risk', type=float, default=0.01, help='Riesgo por operación')
    parser.add_argument('--ratio', type=int, default=4, help='Ratio TP/SL')
    parser.add_argument('--years', type=int, default=2, help='Años de backtesting')
    parser.add_argument('--m15', type=int, default=16, help='Velas M15')
    parser.add_argument('--m1', type=int, default=9, help='Velas M1')
    
    args = parser.parse_args()
    
    print("🤖 BACKTESTING AVANZADO - 4 AÑOS DE DATOS")
    print("=" * 60)
    
    # Crear instancia del backtest
    backtest = FourYearBacktest(
        symbol=args.symbol,
        capital_inicial=args.capital,
        risk=args.risk
    )
    
    # Ejecutar backtesting completo
    resultados = backtest.ejecutar_backtest_completo(
        años=args.years,
        ratio=args.ratio,
        velas_15M=args.m15,
        velas_1M=args.m1
    )
    
    if resultados:
        print("\n🎉 BACKTESTING COMPLETADO EXITOSAMENTE!")
        print(f"📈 Período: {args.years} años")
        print(f"💰 Capital final: ${resultados['resultados']['capital_final']:,.2f}")
        print(f"📊 Profit Factor: {resultados['profit_factor']:.2f}")
    else:
        print("\n❌ El backtesting no pudo completarse")

if __name__ == "__main__":
    main()