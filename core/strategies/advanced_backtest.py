import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse
import time
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class AdvancedICTBacktest:
    def __init__(self, symbol, capital_inicial=10000, risk=0.01):
        # self.symbol = self.ajustar_simbolo(symbol)
        self.symbol = "EURUSDm"
        self.capital_inicial = capital_inicial
        self.risk = risk
        self.tamcontrato = 100000
        self.decimal = 0.0001
        
    def ajustar_simbolo(self, symbol):
        """Ajusta el símbolo para MT5 (remueve la 'm' final)"""
        if symbol.upper().endswith('M'):
            return symbol.upper()[:-1]  # Remueve la 'm' final
        return symbol.upper()
    
    def inicializar_mt5(self):
        """Inicializa la conexión con MetaTrader 5"""
        if not mt5.initialize():
            print("Error al inicializar MT5")
            return False
        
        # Verificar que el terminal esté conectado
        if not mt5.terminal_info():
            print("MT5 no está conectado al servidor")
            return False
            
        print("✅ Conexión con MT5 establecida")
        return True
    
    def verificar_simbolo(self):
        """Verifica y selecciona el símbolo en Market Watch"""
        print(f"🔍 Verificando símbolo: {self.symbol}")
        
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            print(f"❌ El símbolo {self.symbol} no se encuentra")
            
            # Buscar símbolos alternativos
            simbolos_disponibles = self.buscar_simbolos_alternativos()
            if simbolos_disponibles:
                print("📋 Símbolos disponibles similares:")
                for simbolo in simbolos_disponibles[:5]:
                    print(f"   - {simbolo}")
            return False
        
        if not symbol_info.visible:
            print(f"⚠️ El símbolo {self.symbol} no está en Market Watch. Agregando...")
            if not mt5.symbol_select(self.symbol, True):
                print(f"❌ No se pudo agregar {self.symbol} a Market Watch")
                return False
            print(f"✅ Símbolo {self.symbol} agregado a Market Watch")
        else:
            print(f"✅ Símbolo {self.symbol} disponible")
        
        return True
    
    def buscar_simbolos_alternativos(self):
        """Busca símbolos alternativos disponibles"""
        try:
            symbols = mt5.symbols_get()
            if not symbols:
                return []
            
            # Buscar símbolos que contengan EURUSD
            alternativos = []
            for s in symbols:
                if "EURUSDm" in s.name.upper():
                    alternativos.append(s.name)
            
            return alternativos[:10]  # Devolver solo los primeros 10
        except:
            return []
    
    def obtener_datos_rango(self, start_date, end_date):
        """Obtiene datos históricos de MT5 con múltiples métodos"""
        print(f"📥 Solicitando datos desde {start_date} hasta {end_date}")
        
        # Método 1: copy_rates_range
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, start_timestamp, end_timestamp)
        
        if rates is not None and len(rates) > 0:
            print(f"✅ Método 1 exitoso: {len(rates)} velas obtenidas")
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        
        print("⚠️ Método 1 falló, intentando método alternativo...")
        
        # Método 2: copy_rates_from_pos
        days_diff = (end_date - start_date).days
        total_velas = days_diff * 1440  # Velas M1 por día
        
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, total_velas)
        
        if rates is not None and len(rates) > 0:
            print(f"✅ Método 2 exitoso: {len(rates)} velas obtenidas")
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Filtrar por rango de fechas
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            return df
        
        print("❌ Ambos métodos fallaron para obtener datos")
        return None
    
    def obtener_datos_por_partes(self, start_date, end_date):
        """Obtiene datos por partes si el rango es muy grande"""
        print("🔄 Descargando datos por partes...")
        
        current_start = start_date
        all_data = []
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=30), end_date)
            
            print(f"📥 Descargando {current_start.date()} a {current_end.date()}...")
            
            start_timestamp = int(current_start.timestamp())
            end_timestamp = int(current_end.timestamp())
            
            rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, start_timestamp, end_timestamp)
            
            if rates is not None and len(rates) > 0:
                df_part = pd.DataFrame(rates)
                df_part['time'] = pd.to_datetime(df_part['time'], unit='s')
                df_part.set_index('time', inplace=True)
                all_data.append(df_part)
                print(f"   ✅ {len(rates)} velas descargadas")
            else:
                print(f"   ❌ No se pudieron obtener datos para este período")
            
            current_start = current_end + timedelta(days=1)
            time.sleep(0.1)  # Pequeña pausa
        
        if not all_data:
            return None
        
        # Combinar todos los datos
        final_df = pd.concat(all_data)
        final_df = final_df[~final_df.index.duplicated(keep='first')]
        final_df = final_df.sort_index()
        
        return final_df
    
    def calcular_atr(self, df, period=14):
        """Calcula el Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        atr = tr.rolling(period).mean()
        return atr
    
    def ejecutar_estrategia_ict(self, data, ratio, velas_primaria, velas_secundaria):
        """
        Ejecuta la estrategia ICT con configuraciones específicas
        """
        try:
            # Crear copia de datos
            data = data.copy()
            
            # Calcular ATR y slippage
            data['ATR'] = self.calcular_atr(data)
            data['slippage'] = data['ATR'] * 0.003
            
            # Resample para temporalidad primaria
            data_primaria = data.resample(f'{velas_primaria}min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min', 
                'close': 'last'
            }).dropna()
            
            # Calcular rangos por día para temporalidad primaria (antes de 20:00)
            from datetime import time
            data_primaria_filtrado = data_primaria[data_primaria.index.time < time(20, 0)]
            grupos_por_dia = data_primaria_filtrado.groupby(data_primaria_filtrado.index.date)
            
            rangos_por_dia = {}
            for fecha, grupo in grupos_por_dia:
                if len(grupo) >= 3:
                    ultimas_velas = grupo.tail(3)
                    rangos_por_dia[fecha] = {
                        'min': ultimas_velas['low'].min(),
                        'max': ultimas_velas['high'].max()
                    }
            
            # Ejecutar estrategia
            cash = self.capital_inicial
            operations = []
            open_trades = []
            
            for i in range(1, len(data)):
                try:
                    date = data.index[i]
                    close_price = data['close'].iloc[i]
                    low_price = data['low'].iloc[i]
                    high_price = data['high'].iloc[i]
                    hora_actual = date.time()
                    
                    # Cerrar operaciones existentes
                    for operacion in open_trades[:]:
                        cerrar = False
                        precio_salida = None
                        
                        if operacion['Tipo'] == 'short':
                            if low_price <= operacion['TP']:
                                precio_salida = operacion['TP']
                                cerrar = True
                            elif high_price >= operacion['SL']:
                                precio_salida = operacion['SL']
                                cerrar = True
                        else:  # long
                            if high_price >= operacion['TP']:
                                precio_salida = operacion['TP']
                                cerrar = True
                            elif low_price <= operacion['SL']:
                                precio_salida = operacion['SL']
                                cerrar = True
                        
                        if cerrar:
                            if operacion['Tipo'] == 'short':
                                resultado = (operacion['Precio_entrada'] - precio_salida) * operacion['Cantidad'] * self.tamcontrato
                            else:
                                resultado = (precio_salida - operacion['Precio_entrada']) * operacion['Cantidad'] * self.tamcontrato
                            
                            cash += resultado
                            operacion['Fecha_salida'] = date
                            operacion['Precio_salida'] = precio_salida
                            operacion['Resultado'] = resultado
                            operations.append(operacion)
                            open_trades.remove(operacion)
                    
                    # Abrir nuevas operaciones (20:00 - 22:00)
                    if (time(20, 0) <= hora_actual < time(22, 0) and 
                        len(open_trades) == 0):
                        
                        fecha_clave = date.date()
                        if fecha_clave not in rangos_por_dia:
                            continue
                            
                        rango = rangos_por_dia[fecha_clave]
                        
                        # Señal SHORT
                        if high_price > rango['max']:
                            # Verificar en temporalidad secundaria
                            idx_actual = data.index.get_loc(date)
                            inicio = max(0, idx_actual - velas_secundaria)
                            velas_secundaria_data = data.iloc[inicio:idx_actual]
                            
                            if len(velas_secundaria_data) > 0 and close_price < velas_secundaria_data['low'].min():
                                # Calcular entrada, SL, TP
                                current_day = date.date()
                                velas_desde_20 = data.loc[
                                    (data.index.date == current_day) & 
                                    (data.index.time >= time(20, 0)) & 
                                    (data.index <= date)
                                ]
                                
                                if len(velas_desde_20) > 0:
                                    max_desde_20 = velas_desde_20['high'].max()
                                    risk_amount = cash * self.risk
                                    
                                    entry_price = close_price
                                    sl_price = max_desde_20 + self.decimal * 50
                                    tp_price = entry_price - abs(entry_price - sl_price) * ratio
                                    
                                    # Aplicar costos
                                    spread = data['spread'].iloc[idx_actual] * self.decimal if 'spread' in data.columns else 0.0001
                                    slippage = data['slippage'].iloc[idx_actual] if 'slippage' in data.columns else 0.0001
                                    entry_price += spread + slippage
                                    
                                    # Calcular tamaño posición
                                    riesgo_por_contrato = abs(entry_price - sl_price) * self.tamcontrato
                                    if riesgo_por_contrato > 0:
                                        cantidad = risk_amount / riesgo_por_contrato
                                        cantidad = max(0.01, min(cantidad, 10))
                                        
                                        operacion = {
                                            'Fecha_entrada': date,
                                            'Tipo': 'short',
                                            'Precio_entrada': entry_price,
                                            'SL': sl_price,
                                            'TP': tp_price,
                                            'Cantidad': cantidad,
                                            'Configuracion': f'R{ratio}/{velas_primaria}M/{velas_secundaria}M'
                                        }
                                        open_trades.append(operacion)
                                        continue
                        
                        # Señal LONG
                        if low_price < rango['min']:
                            idx_actual = data.index.get_loc(date)
                            inicio = max(0, idx_actual - velas_secundaria)
                            velas_secundaria_data = data.iloc[inicio:idx_actual]
                            
                            if len(velas_secundaria_data) > 0 and close_price > velas_secundaria_data['high'].max():
                                current_day = date.date()
                                velas_desde_20 = data.loc[
                                    (data.index.date == current_day) & 
                                    (data.index.time >= time(20, 0)) & 
                                    (data.index <= date)
                                ]
                                
                                if len(velas_desde_20) > 0:
                                    min_desde_20 = velas_desde_20['low'].min()
                                    risk_amount = cash * self.risk
                                    
                                    entry_price = close_price
                                    sl_price = min_desde_20 - self.decimal * 50
                                    tp_price = entry_price + abs(entry_price - sl_price) * ratio
                                    
                                    spread = data['spread'].iloc[idx_actual] * self.decimal if 'spread' in data.columns else 0.0001
                                    slippage = data['slippage'].iloc[idx_actual] if 'slippage' in data.columns else 0.0001
                                    entry_price -= spread + slippage
                                    
                                    riesgo_por_contrato = abs(entry_price - sl_price) * self.tamcontrato
                                    if riesgo_por_contrato > 0:
                                        cantidad = risk_amount / riesgo_por_contrato
                                        cantidad = max(0.01, min(cantidad, 10))
                                        
                                        operacion = {
                                            'Fecha_entrada': date,
                                            'Tipo': 'long',
                                            'Precio_entrada': entry_price,
                                            'SL': sl_price,
                                            'TP': tp_price,
                                            'Cantidad': cantidad,
                                            'Configuracion': f'R{ratio}/{velas_primaria}M/{velas_secundaria}M'
                                        }
                                        open_trades.append(operacion)
                
                except Exception as e:
                    continue
            
            # Cerrar operaciones pendientes al final
            for operacion in open_trades:
                ultimo_precio = data['close'].iloc[-1]
                if operacion['Tipo'] == 'short':
                    resultado = (operacion['Precio_entrada'] - ultimo_precio) * operacion['Cantidad'] * self.tamcontrato
                else:
                    resultado = (ultimo_precio - operacion['Precio_entrada']) * operacion['Cantidad'] * self.tamcontrato
                
                cash += resultado
                operacion['Fecha_salida'] = data.index[-1]
                operacion['Precio_salida'] = ultimo_precio
                operacion['Resultado'] = resultado
                operations.append(operacion)
            
            # Calcular métricas
            if operations:
                resultados = [op['Resultado'] for op in operations]
                ganancias = [r for r in resultados if r > 0]
                perdidas = [r for r in resultados if r < 0]
                
                total_ganancias = sum(ganancias) if ganancias else 0
                total_perdidas = abs(sum(perdidas)) if perdidas else 0
                
                profit_factor = total_ganancias / total_perdidas if total_perdidas > 0 else float('inf')
                win_rate = len(ganancias) / len(operations) * 100
                profit_total = cash - self.capital_inicial
                
            else:
                profit_factor = 0
                win_rate = 0
                profit_total = 0
            
            return {
                'configuracion': f'R{ratio}/{velas_primaria}M/{velas_secundaria}M',
                'profit_factor': profit_factor,
                'win_rate': win_rate,
                'profit_total': profit_total,
                'total_operaciones': len(operations),
                'operaciones_ganadas': len([r for r in operations if r['Resultado'] > 0]),
                'capital_final': cash,
                'operations': operations
            }
            
        except Exception as e:
            print(f"❌ Error en estrategia {ratio}/{velas_primaria}M/{velas_secundaria}M: {e}")
            return None
    
    def generar_configuraciones(self):
        """Genera todas las configuraciones a probar"""
        ratios = [1, 2, 3, 4, 5]  # R1 a R5
        
        configuraciones = []
        
        for ratio in ratios:
            configuraciones.extend([
                (ratio, 7, 7),   # R1/7M/7M
                (ratio, 7, 11),  # R1/7M/11M
                (ratio, 7, 15),  # R1/7M/15M
                (ratio, 10, 9),  # R1/10M/9M
                (ratio, 10, 13), # R1/10M/13M
                (ratio, 13, 7),  # R1/13M/7M
                (ratio, 13, 11), # R1/13M/11M
                (ratio, 13, 15), # R1/13M/15M
                (ratio, 16, 9),  # R1/16M/9M
                (ratio, 16, 13), # R1/16M/13M
                (ratio, 19, 7),  # R1/19M/7M
                (ratio, 19, 11), # R1/19M/11M
                (ratio, 19, 15), # R1/19M/15M
                (ratio, 22, 9),  # R1/22M/9M
                (ratio, 22, 13), # R1/22M/13M
                (ratio, 25, 7),  # R1/25M/7M
                (ratio, 25, 11), # R1/25M/11M
                (ratio, 25, 15), # R1/25M/15M
                (ratio, 28, 9),  # R1/28M/9M
                (ratio, 28, 13), # R1/28M/13M
            ])
        
        return configuraciones
    
    def ejecutar_backtest_completo(self, meses=6):
        """Ejecuta backtesting completo para todas las configuraciones"""
        print("🔍 INICIANDO BACKTESTING AVANZADO ICT")
        print("=" * 60)
        
        if not self.inicializar_mt5():
            return None
        
        try:
            # Verificar símbolo
            if not self.verificar_simbolo():
                print("❌ No se pudo verificar el símbolo")
                return None
            
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=meses * 30)
            
            print(f"📅 Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            print(f"💰 Capital inicial: ${self.capital_inicial:,.2f}")
            print(f"🎯 Símbolo: {self.symbol}")
            print(f"⏰ Duración: {meses} meses")
            print("=" * 60)
            
            # Obtener datos
            print("📥 Descargando datos históricos...")
            data = self.obtener_datos_rango(start_date, end_date)
            
            if data is None:
                print("⚠️ Intentando descarga por partes...")
                data = self.obtener_datos_por_partes(start_date, end_date)
            
            if data is None or len(data) == 0:
                print("❌ No se pudieron obtener datos históricos")
                return None
            
            print(f"✅ Datos obtenidos: {len(data)} velas M1")
            print(f"📊 Rango de datos: {data.index[0]} a {data.index[-1]}")
            
            # Asegurar columnas necesarias
            if 'spread' not in data.columns:
                data['spread'] = 10
            
            # Generar configuraciones
            configuraciones = self.generar_configuraciones()
            print(f"🔄 Probando {len(configuraciones)} configuraciones...")
            
            resultados = []
            
            for i, (ratio, primaria, secundaria) in enumerate(configuraciones, 1):
                print(f"🔧 Ejecutando {i}/{len(configuraciones)}: R{ratio}/{primaria}M/{secundaria}M")
                
                resultado = self.ejecutar_estrategia_ict(data, ratio, primaria, secundaria)
                if resultado:
                    resultados.append(resultado)
                
                # Pequeña pausa para no sobrecargar
                time.sleep(0.1)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en backtesting completo: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            mt5.shutdown()
            print("🔌 Conexión con MT5 cerrada")
    
    def analizar_resultados(self, resultados):
        """Analiza y muestra los resultados del backtesting"""
        if not resultados:
            print("❌ No hay resultados para analizar")
            return None
        
        print("\n" + "=" * 80)
        print("📊 RESULTADOS BACKTESTING AVANZADO ICT")
        print("=" * 80)
        
        # Crear DataFrame con resultados
        df_resultados = pd.DataFrame([{
            'Configuracion': r['configuracion'],
            'Profit_Factor': r['profit_factor'],
            'Win_Rate': r['win_rate'],
            'Profit_Total': r['profit_total'],
            'Total_Operaciones': r['total_operaciones'],
            'Operaciones_Ganadas': r['operaciones_ganadas'],
            'Capital_Final': r['capital_final']
        } for r in resultados])
        
        # Ordenar por Profit Factor descendente
        df_resultados = df_resultados.sort_values('Profit_Factor', ascending=False)
        
        # Mostrar mejores configuraciones
        print("\n🏆 TOP 10 MEJORES CONFIGURACIONES:")
        print("-" * 80)
        print(df_resultados.head(10).to_string(index=False, float_format='%.3f'))
        
        # Análisis por Ratio
        print("\n📈 ANÁLISIS POR RATIO:")
        print("-" * 40)
        
        for ratio in [1, 2, 3, 4, 5]:
            configs_ratio = [r for r in resultados if r['configuracion'].startswith(f'R{ratio}/')]
            if configs_ratio:
                profit_factors = [r['profit_factor'] for r in configs_ratio if r['profit_factor'] != float('inf')]
                if profit_factors:
                    avg_pf = np.mean(profit_factors)
                    max_pf = max(profit_factors)
                    min_pf = min(profit_factors)
                    print(f"R{ratio}: Avg PF: {avg_pf:.3f} | Max PF: {max_pf:.3f} | Min PF: {min_pf:.3f} | Configs: {len(configs_ratio)}")
        
        return df_resultados
    
    def generar_grafica_profit_factor(self, df_resultados):
        """Genera gráfica de Profit Factor por Configuración"""
        try:
            # Preparar datos para la gráfica
            configuraciones = df_resultados['Configuracion'].tolist()
            profit_factors = df_resultados['Profit_Factor'].tolist()
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(16, 10))
            
            # Gráfica de barras
            bars = ax.bar(configuraciones, profit_factors, 
                         color=['#2E86AB' if pf >= 1 else '#A23B72' for pf in profit_factors],
                         alpha=0.7)
            
            # Línea de profit factor = 1 (break-even)
            ax.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Break-even (PF=1)')
            
            # Configurar ejes
            ax.set_ylabel('Profit Factor', fontsize=12, fontweight='bold')
            ax.set_xlabel('Configuración (Ratio/Temp_Primaria/Temp_Secundaria)', fontsize=12, fontweight='bold')
            ax.set_title('Profit Factor por Configuración - Estrategia ICT', 
                        fontsize=14, fontweight='bold', pad=20)
            
            # Rotar etiquetas del eje X para mejor legibilidad
            plt.xticks(rotation=45, ha='right')
            
            # Añadir grid
            ax.grid(True, alpha=0.3, axis='y')
            
            # Añadir leyenda
            ax.legend()
            
            # Ajustar layout
            plt.tight_layout()
            
            # Guardar gráfica
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"profit_factor_ict_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"✅ Gráfica guardada como: {filename}")
            
            return fig
            
        except Exception as e:
            print(f"❌ Error generando gráfica: {e}")
            return None
    
    def generar_grafica_media_ratio(self, df_resultados):
        """Genera gráfica de media por Ratio (como en tu imagen)"""
        try:
            # Calcular promedio de profit factor por ratio
            ratios = []
            promedios = []
            
            for ratio in [1, 2, 3, 4, 5]:
                configs_ratio = df_resultados[df_resultados['Configuracion'].str.startswith(f'R{ratio}/')]
                if not configs_ratio.empty:
                    avg_pf = configs_ratio['Profit_Factor'].mean()
                    ratios.append(f'R{ratio}')
                    promedios.append(avg_pf)
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Gráfica de líneas
            ax.plot(ratios, promedios, marker='o', linewidth=3, markersize=8, 
                   color='#2E86AB', alpha=0.8)
            
            # Rellenar área bajo la curva
            ax.fill_between(ratios, promedios, alpha=0.2, color='#2E86AB')
            
            # Configurar ejes
            ax.set_ylabel('Profit Factor Promedio', fontsize=12, fontweight='bold')
            ax.set_xlabel('Ratio', fontsize=12, fontweight='bold')
            ax.set_title('Profit Factor Promedio por Ratio - Estrategia ICT', 
                        fontsize=14, fontweight='bold', pad=20)
            
            # Añadir valores en los puntos
            for i, (ratio, valor) in enumerate(zip(ratios, promedios)):
                ax.annotate(f'{valor:.2f}', (ratio, valor), 
                           textcoords="offset points", xytext=(0,10), 
                           ha='center', fontweight='bold')
            
            # Grid y estilo
            ax.grid(True, alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Ajustar límites del eje Y
            y_min = min(promedios) * 0.8
            y_max = max(promedios) * 1.2
            ax.set_ylim(y_min, y_max)
            
            plt.tight_layout()
            
            # Guardar gráfica
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"media_ratio_ict_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"✅ Gráfica de media por ratio guardada como: {filename}")
            
            return fig
            
        except Exception as e:
            print(f"❌ Error generando gráfica de media: {e}")
            return None

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Backtesting Avanzado ICT')
    parser.add_argument('--symbol', type=str, default='EURUSDm', help='Símbolo a operar')
    parser.add_argument('--capital', type=float, default=10000, help='Capital inicial')
    parser.add_argument('--risk', type=float, default=0.01, help='Riesgo por operación')
    parser.add_argument('--meses', type=int, default=3, help='Meses de backtesting')  # Reducido por defecto
    
    args = parser.parse_args()
    
    # Crear y ejecutar backtesting
    backtest = AdvancedICTBacktest(
        symbol="EURUSDm",
        capital_inicial=args.capital,
        risk=args.risk
    )
    
    # Ejecutar backtesting completo
    resultados = backtest.ejecutar_backtest_completo(meses=args.meses)
    
    if resultados:
        # Analizar resultados
        df_resultados = backtest.analizar_resultados(resultados)
        
        # Generar gráficas
        backtest.generar_grafica_profit_factor(df_resultados)
        backtest.generar_grafica_media_ratio(df_resultados)
        
        print(f"\n🎉 Backtesting completado exitosamente!")
        print(f"📈 Se probaron {len(resultados)} configuraciones")
        print(f"💰 Mejor Profit Factor: {df_resultados['Profit_Factor'].max():.3f}")
        
    else:
        print("❌ No se pudieron obtener resultados del backtesting")

if __name__ == "__main__":
    main()