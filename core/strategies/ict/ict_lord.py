# strategy_ict_continuous.py
# Estrategia de ICT mejorada con ejecución continua y capital dinámico
import talib
from datetime import time, datetime
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class StrategyICTContinuous:
    def __init__(self, data, symbol, decimal, swap, tamcontrato, 
                 velas_15M=9, velas_1M=16, ratio=5, risk=0.01, initial_cash=100,
                 max_operaciones_abiertas=3, distancia_minima_entre_operaciones=5):
        
        self.data = data.copy()
        
        # Parámetros de la estrategia
        self.velas_m15 = velas_15M
        self.velas_m1 = velas_1M
        self.ratio = ratio
        self.risk = risk
        
        # Configuraciones de gestión de riesgo
        self.max_operaciones_abiertas = max_operaciones_abiertas
        self.distancia_minima_entre_operaciones = distancia_minima_entre_operaciones  # en minutos
        
        # Configuraciones DINÁMICAS
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.operations = []
        self.symbol = symbol
        self.decimal = decimal
        self.tamcontrato = tamcontrato
        self.swap = swap
        self.position = 0
        self.open_trades = []
        self.capital_evolution = [initial_cash]  # Evolución del capital
        self.trade_count_evolution = [0]  # Conteo de operaciones
        self.ultima_operacion_time = None  # Para control de frecuencia
        
        # Calcular ATR y slippage
        self.data['ATR'] = talib.ATR(self.data['high'], self.data['low'], 
                                    self.data['close'], timeperiod=14)
        self.data['slippage'] = self.data['ATR'] * 0.003
        
        # Calcular rangos por día para M15 (actualizado continuamente)
        self._calcular_rangos_m15_continuo()
    
    def _calcular_rangos_m15_continuo(self):
        """Calcula máximos y mínimos de las últimas velas M15 de forma continua"""
        try:
            # Resample a 15 minutos
            data_m15 = self.data.resample('15min').agg({
                'open': 'first',
                'high': 'max', 
                'low': 'min',
                'close': 'last'
            }).dropna()
            
            # Agrupar por día (ahora usamos todo el día para rangos dinámicos)
            grupos_por_dia = data_m15.groupby(data_m15.index.date)
            
            # Diccionario para guardar datos por día
            self.rangos_por_dia = {}
            
            for fecha, grupo in grupos_por_dia:
                if len(grupo) >= self.velas_m15:
                    # Usamos las últimas N velas M15 del día (no solo antes de 20:00)
                    ultimas_velas = grupo.tail(self.velas_m15)
                    minimo = ultimas_velas['low'].min()
                    maximo = ultimas_velas['high'].max()
                    self.rangos_por_dia[fecha] = {
                        'min': minimo, 
                        'max': maximo,
                        'ultima_actualizacion': ultimas_velas.index[-1]
                    }
                    
            print(f"✅ Rangos M15 calculados para {len(self.rangos_por_dia)} días")
            
        except Exception as e:
            print(f"Error calculando rangos M15 continuos: {e}")
            self.rangos_por_dia = {}
    
    def _puede_abrir_operacion(self, current_time):
        """Verifica si se puede abrir una nueva operación según las reglas"""
        # Verificar límite de operaciones abiertas
        if len(self.open_trades) >= self.max_operaciones_abiertas:
            return False, "Límite de operaciones abiertas alcanzado"
        
        # Verificar distancia mínima entre operaciones
        if self.ultima_operacion_time is not None:
            tiempo_desde_ultima = (current_time - self.ultima_operacion_time).total_seconds() / 60
            if tiempo_desde_ultima < self.distancia_minima_entre_operaciones:
                return False, f"Esperando {self.distancia_minima_entre_operaciones} minutos entre operaciones"
        
        return True, "Puede abrir operación"
    
    def _calcular_tamaño_posicion(self, entry_price, sl_price):
        """Calcula el tamaño de la posición basado en el riesgo DINÁMICO"""
        risk_amount = self.cash * self.risk
        riesgo_por_contrato = abs(entry_price - sl_price) * self.tamcontrato
        
        if riesgo_por_contrato > 0:
            tamaño = (risk_amount / riesgo_por_contrato)
            # Ajustar a tamaño mínimo y máximo razonable
            tamaño = max(0.01, min(tamaño, self.cash * 0.1 / riesgo_por_contrato))
            return round(tamaño, 2)
        return 0.01
    
    def _actualizar_evolucion_capital(self):
        """Actualiza la evolución del capital después de cada operación"""
        self.capital_evolution.append(self.cash)
        self.trade_count_evolution.append(len(self.operations))
    
    def _evaluar_señal_corta_continua(self, date, close_price, low_price, high_price):
        """Evalúa señal de venta (SHORT) de forma continua"""
        fecha_clave = date.date()
        
        if fecha_clave not in self.rangos_por_dia:
            return None
            
        rango = self.rangos_por_dia[fecha_clave]
        
        # Señal SHORT: Precio rompe máximo de M15 y luego cierra por debajo del mínimo de M1
        if high_price > rango['max']:
            try:
                idx_actual = self.data.index.get_loc(date)
                inicio = max(0, idx_actual - self.velas_m1)
                ultimas_velas_1M = self.data.iloc[inicio:idx_actual]
                
                if len(ultimas_velas_1M) > 0 and close_price < ultimas_velas_1M['low'].min():
                    # Calcular SL como máximo de las últimas velas (no solo desde 20:00)
                    lookback_sl = min(50, idx_actual)  # Máximo 50 velas hacia atrás
                    velas_para_sl = self.data.iloc[idx_actual - lookback_sl:idx_actual]
                    
                    if len(velas_para_sl) > 0:
                        max_para_sl = velas_para_sl['high'].max()
                        decimales = abs(int(round(-math.log10(self.decimal))))
                        
                        entry_price = round(close_price, decimales)
                        sl_price = round(max_para_sl, decimales) + self.decimal * 50
                        tp_price = round(entry_price - abs(entry_price - sl_price) * self.ratio, decimales)
                        
                        # Aplicar spread y slippage
                        spread = self.data['spread'].iloc[idx_actual] * self.decimal
                        slippage_value = max(self.data['slippage'].iloc[idx_actual], self.decimal)
                        entry_price += spread + slippage_value
                        entry_price = round(entry_price, decimales)
                        
                        position_size = self._calcular_tamaño_posicion(entry_price, sl_price)
                        
                        return {
                            'Fecha de entrada': date,
                            'Max 15M': rango['max'],
                            'Min 15M': rango['min'],
                            'Max/Min 1M': ultimas_velas_1M['low'].min(),
                            'Tipo': 'short',
                            'Precio de entrada': entry_price,
                            'SL': sl_price,
                            'TP': tp_price,
                            'Cantidad': position_size,
                            'Fecha de salida': None,
                            'Resultado': None,
                            'Precio salida': None,
                            'Capital antes': self.cash
                        }
            except Exception as e:
                print(f"Error en señal corta continua: {e}")
                return None
        return None
    
    def _evaluar_señal_larga_continua(self, date, close_price, low_price, high_price):
        """Evalúa señal de compra (LONG) de forma continua"""
        fecha_clave = date.date()
        
        if fecha_clave not in self.rangos_por_dia:
            return None
            
        rango = self.rangos_por_dia[fecha_clave]
        
        # Señal LONG: Precio rompe mínimo de M15 y luego cierra por encima del máximo de M1
        if low_price < rango['min']:
            try:
                idx_actual = self.data.index.get_loc(date)
                inicio = max(0, idx_actual - self.velas_m1)
                ultimas_velas_1M = self.data.iloc[inicio:idx_actual]
                
                if len(ultimas_velas_1M) > 0 and close_price > ultimas_velas_1M['high'].max():
                    # Calcular SL como mínimo de las últimas velas (no solo desde 20:00)
                    lookback_sl = min(50, idx_actual)  # Máximo 50 velas hacia atrás
                    velas_para_sl = self.data.iloc[idx_actual - lookback_sl:idx_actual]
                    
                    if len(velas_para_sl) > 0:
                        min_para_sl = velas_para_sl['low'].min()
                        decimales = abs(int(round(-math.log10(self.decimal))))
                        
                        entry_price = round(close_price, decimales)
                        sl_price = round(min_para_sl, decimales) - self.decimal * 50
                        tp_price = round(entry_price + abs(entry_price - sl_price) * self.ratio, decimales)
                        
                        # Aplicar spread y slippage
                        spread = self.data['spread'].iloc[idx_actual] * self.decimal
                        slippage_value = max(self.data['slippage'].iloc[idx_actual], self.decimal)
                        entry_price -= spread + slippage_value
                        entry_price = round(entry_price, decimales)
                        
                        position_size = self._calcular_tamaño_posicion(entry_price, sl_price)
                        
                        return {
                            'Fecha de entrada': date,
                            'Max 15M': rango['max'],
                            'Min 15M': rango['min'],
                            'Max/Min 1M': ultimas_velas_1M['high'].max(),
                            'Tipo': 'long',
                            'Precio de entrada': entry_price,
                            'SL': sl_price,
                            'TP': tp_price,
                            'Cantidad': position_size,
                            'Fecha de salida': None,
                            'Resultado': None,
                            'Precio salida': None,
                            'Capital antes': self.cash
                        }
            except Exception as e:
                print(f"Error en señal larga continua: {e}")
                return None
        return None
    
    def _cerrar_operaciones(self, date, high_price, low_price):
        """Cierra operaciones que alcanzan SL o TP"""
        operaciones_cerradas = []
        
        for operacion in self.open_trades[:]:
            cerrar_operacion = False
            precio_salida = None
            resultado = 0
            
            try:
                if operacion['Tipo'] == 'short':
                    if low_price <= operacion['TP']:
                        precio_salida = operacion['TP']
                        resultado = (operacion['Precio de entrada'] - precio_salida) * operacion['Cantidad'] * self.tamcontrato
                        cerrar_operacion = True
                    elif high_price >= operacion['SL']:
                        precio_salida = operacion['SL']
                        resultado = (operacion['Precio de entrada'] - precio_salida) * operacion['Cantidad'] * self.tamcontrato
                        cerrar_operacion = True
                        
                elif operacion['Tipo'] == 'long':
                    if high_price >= operacion['TP']:
                        precio_salida = operacion['TP']
                        resultado = (precio_salida - operacion['Precio de entrada']) * operacion['Cantidad'] * self.tamcontrato
                        cerrar_operacion = True
                    elif low_price <= operacion['SL']:
                        precio_salida = operacion['SL']
                        resultado = (precio_salida - operacion['Precio de entrada']) * operacion['Cantidad'] * self.tamcontrato
                        cerrar_operacion = True
                
                if cerrar_operacion:
                    operacion['Fecha de salida'] = date
                    operacion['Precio salida'] = precio_salida
                    operacion['Resultado'] = resultado
                    self.cash += resultado
                    self.operations.append(operacion)
                    self.open_trades.remove(operacion)
                    operaciones_cerradas.append(operacion)
                    
                    # Actualizar evolución del capital
                    self._actualizar_evolucion_capital()
                    
                    print(f"🔒 Operación {operacion['Tipo']} cerrada: ${resultado:+.2f} | Capital: ${self.cash:,.2f}")
                    
            except Exception as e:
                print(f"Error cerrando operación: {e}")
                continue
        
        return operaciones_cerradas
    
    def run_continuous(self):
        """Ejecuta la estrategia de forma continua (sin restricción de horario)"""
        print("🔄 Ejecutando estrategia ICT CONTINUA...")
        print(f"📊 Parámetros: M15={self.velas_m15}, M1={self.velas_m1}, Ratio={self.ratio}")
        print(f"⚙️  Configuración: Máx operaciones={self.max_operaciones_abiertas}, Distancia mínima={self.distancia_minima_entre_operaciones}min")
        
        total_señales = 0
        señales_ejecutadas = 0
        
        for i in range(1, len(self.data)):
            try:
                date = self.data.index[i]
                close_price = self.data['close'].iloc[i]
                low_price = self.data['low'].iloc[i]
                high_price = self.data['high'].iloc[i]
                
                # 1. Cerrar operaciones existentes si alcanzan SL/TP
                operaciones_cerradas = self._cerrar_operaciones(date, high_price, low_price)
                
                # 2. Verificar si podemos abrir nueva operación
                puede_abrir, razon = self._puede_abrir_operacion(date)
                
                if puede_abrir:
                    # 3. Evaluar señales SHORT y LONG de forma continua
                    señal_corta = self._evaluar_señal_corta_continua(date, close_price, low_price, high_price)
                    señal_larga = self._evaluar_señal_larga_continua(date, close_price, low_price, high_price)
                    
                    total_señales += 1
                    
                    # 4. Ejecutar la primera señal que ocurra
                    if señal_corta:
                        self.open_trades.append(señal_corta)
                        self.ultima_operacion_time = date
                        señales_ejecutadas += 1
                        print(f"📉 [{date.strftime('%Y-%m-%d %H:%M')}] Señal SHORT ejecutada | "
                              f"Capital: ${self.cash:,.2f} | Size: {señal_corta['Cantidad']:.2f}")
                              
                    elif señal_larga:
                        self.open_trades.append(señal_larga)
                        self.ultima_operacion_time = date
                        señales_ejecutadas += 1
                        print(f"📈 [{date.strftime('%Y-%m-%d %H:%M')}] Señal LONG ejecutada | "
                              f"Capital: ${self.cash:,.2f} | Size: {señal_larga['Cantidad']:.2f}")
                
                # Log periódico del progreso
                if i % 10000 == 0:
                    print(f"📊 Progreso: {i}/{len(self.data)} velas | "
                          f"Operaciones: {len(self.operations)} cerradas, {len(self.open_trades)} abiertas")
                            
            except Exception as e:
                print(f"❌ Error procesando vela {i}: {e}")
                continue
        
        # Cerrar todas las operaciones abiertas al final del backtest
        self._cerrar_operaciones_restantes()
        
        print(f"✅ Estrategia continua completada")
        print(f"📈 Señales detectadas: {total_señales} | Ejecutadas: {señales_ejecutadas}")
        
        return self.operations
    
    def _cerrar_operaciones_restantes(self):
        """Cierra todas las operaciones abiertas al final del backtest"""
        for operacion in self.open_trades[:]:
            try:
                ultimo_precio = self.data['close'].iloc[-1]
                resultado = 0
                
                if operacion['Tipo'] == 'short':
                    resultado = (operacion['Precio de entrada'] - ultimo_precio) * operacion['Cantidad'] * self.tamcontrato
                else:
                    resultado = (ultimo_precio - operacion['Precio de entrada']) * operacion['Cantidad'] * self.tamcontrato
                
                operacion['Fecha de salida'] = self.data.index[-1]
                operacion['Precio salida'] = ultimo_precio
                operacion['Resultado'] = resultado
                self.cash += resultado
                self.operations.append(operacion)
                self._actualizar_evolucion_capital()
                
                print(f"🔚 Operación {operacion['Tipo']} cerrada al final: ${resultado:+.2f}")
                
            except Exception as e:
                print(f"Error cerrando operación final: {e}")
                continue
        
        self.open_trades.clear()
    
    def get_results(self):
        """Obtiene resultados detallados de la estrategia"""
        if not self.operations:
            return self._get_empty_results()
        
        operaciones_ganadas = sum(1 for op in self.operations if op['Resultado'] > 0)
        operaciones_perdidas = sum(1 for op in self.operations if op['Resultado'] <= 0)
        profit_total = self.cash - self.initial_cash
        profit_porcentaje = (profit_total / self.initial_cash) * 100
        
        # Calcular métricas adicionales
        resultados = [op['Resultado'] for op in self.operations]
        resultados_positivos = [r for r in resultados if r > 0]
        resultados_negativos = [r for r in resultados if r < 0]
        
        return {
            'capital_inicial': self.initial_cash,
            'capital_final': self.cash,
            'total_operaciones': len(self.operations),
            'operaciones_ganadas': operaciones_ganadas,
            'operaciones_perdidas': operaciones_perdidas,
            'porcentaje_ganadas': (operaciones_ganadas / len(self.operations)) * 100 if self.operations else 0,
            'profit_total': profit_total,
            'profit_percent': profit_porcentaje,
            'profit_promedio': np.mean(resultados_positivos) if resultados_positivos else 0,
            'perdida_promedio': np.mean(resultados_negativos) if resultados_negativos else 0,
            'maxima_ganancia': max(resultados_positivos) if resultados_positivos else 0,
            'maxima_perdida': min(resultados_negativos) if resultados_negativos else 0,
            'ratio_ganancia_perdida': (
                abs(np.mean(resultados_positivos) / np.mean(resultados_negativos)) 
                if resultados_positivos and resultados_negativos and np.mean(resultados_negativos) != 0 
                else 0
            )
        }
    
    def _get_empty_results(self):
        """Retorna resultados vacíos cuando no hay operaciones"""
        return {
            'capital_inicial': self.initial_cash,
            'capital_final': self.cash,
            'total_operaciones': 0,
            'operaciones_ganadas': 0,
            'operaciones_perdidas': 0,
            'porcentaje_ganadas': 0,
            'profit_total': 0,
            'profit_percent': 0,
            'profit_promedio': 0,
            'perdida_promedio': 0,
            'maxima_ganancia': 0,
            'maxima_perdida': 0,
            'ratio_ganancia_perdida': 0
        }
    
    def generar_grafica_evolucion(self, output_file="evolucion_cuenta_continua.png"):
        """Genera gráfica de evolución del capital"""
        try:
            if len(self.capital_evolution) < 2:
                print("No hay suficientes datos para generar la gráfica")
                return None
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Gráfica principal
            ax.plot(self.trade_count_evolution, self.capital_evolution, 
                   linewidth=2.5, color='#2E86AB', alpha=0.8)
            ax.fill_between(self.trade_count_evolution, self.capital_evolution, 
                           alpha=0.2, color='#2E86AB')
            
            # Configurar ejes dinámicamente
            min_capital = min(self.capital_evolution)
            max_capital = max(self.capital_evolution)
            
            # Ajustar límites para mejor visualización
            y_min = min_capital * 0.95
            y_max = max_capital * 1.05
            
            ax.set_ylim(y_min, y_max)
            
            # Crear ticks dinámicos
            y_range = y_max - y_min
            y_step = max(100, y_range / 8)
            y_ticks = np.arange(round(y_min / 100) * 100, y_max, y_step)
            ax.set_yticks(y_ticks)
            ax.set_yticklabels([f'${x:,.0f}' for x in y_ticks])
            
            # Eje X
            max_trades = max(self.trade_count_evolution)
            ax.set_xlim(0, max_trades)
            x_ticks = np.arange(0, max_trades + 1, max(1, max_trades // 10))
            ax.set_xticks(x_ticks)
            ax.set_xlabel('Número de Trades', fontsize=12, fontweight='bold')
            
            ax.set_ylabel('Evolución de la Cuenta ($)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Estadísticas
            capital_final = self.capital_evolution[-1]
            profit_total = capital_final - self.initial_cash
            profit_porcentaje = (profit_total / self.initial_cash) * 100
            
            stats_text = (f'Capital Final: ${capital_final:,.0f}\n'
                         f'Profit: {profit_porcentaje:+.1f}%\n'
                         f'Operaciones: {len(self.operations)}')
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"✅ Gráfica guardada como: {output_file}")
            return fig
            
        except Exception as e:
            print(f"Error generando gráfica: {e}")
            return None

    # Método run para compatibilidad con backtesting existente
    def run(self):
        """Método run para compatibilidad - ejecuta la versión continua"""
        return self.run_continuous()