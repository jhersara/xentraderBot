# strategy_ict.py
# Estrategia de ICT mejorada
import talib
from datetime import time
import math
import pandas as pd
import numpy as np

class StrategyICT:
    def __init__(self, data, symbol, decimal, swap, tamcontrato, 
                 velas_15M=3, velas_1M=30, ratio=2, risk=0.01, initial_cash=10000):
        
        self.data = data.copy()
        
        # Parámetros
        self.velas_m15 = velas_15M
        self.velas_m1 = velas_1M
        self.ratio = ratio
        self.risk = risk
        
        # Configuraciones
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.operations = []
        self.symbol = symbol
        self.decimal = decimal
        self.tamcontrato = tamcontrato
        self.swap = swap
        self.position = 0
        self.open_trades = []
        
        # Calcular ATR y slippage
        self.data['ATR'] = talib.ATR(self.data['high'], self.data['low'], 
                                    self.data['close'], timeperiod=14)
        self.data['slippage'] = self.data['ATR'] * 0.003
        
        # Calcular rangos por día para M15 (antes de las 20:00)
        self._calcular_rangos_m15()
    
    def _calcular_rangos_m15(self):
        """Calcula máximos y mínimos de las últimas velas M15 antes de las 20:00"""
        # Resample a 15 minutos
        data_m15 = self.data.resample('15min').agg({
            'open': 'first',
            'high': 'max', 
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        # Filtrar velas antes de las 20:00
        data_15M_filtrado = data_m15[data_m15.index.time < time(20, 0)]
        
        # Agrupar por día
        grupos_por_dia = data_15M_filtrado.groupby(data_15M_filtrado.index.date)
        
        # Diccionario para guardar datos por día
        self.rangos_por_dia = {}
        
        for fecha, grupo in grupos_por_dia:
            if len(grupo) >= self.velas_m15:
                ultimas_velas = grupo.tail(self.velas_m15)
                minimo = ultimas_velas['low'].min()
                maximo = ultimas_velas['high'].max()
                self.rangos_por_dia[fecha] = {'min': minimo, 'max': maximo}
    
    def _calcular_tamaño_posicion(self, risk_amount, entry_price, sl_price):
        """Calcula el tamaño de la posición basado en el riesgo"""
        riesgo_por_contrato = abs(entry_price - sl_price) * self.tamcontrato
        if riesgo_por_contrato > 0:
            tamaño = (risk_amount / riesgo_por_contrato)
            # Ajustar a tamaño mínimo y máximo razonable
            tamaño = max(0.01, min(tamaño, self.cash * 0.1 / riesgo_por_contrato))
            return round(tamaño, 2)
        return 0.01
    
    def _evaluar_señal_corta(self, date, close_price, low_price, high_price, fecha_clave):
        """Evalúa señal de venta (SHORT)"""
        if fecha_clave not in self.rangos_por_dia:
            return None
            
        rango = self.rangos_por_dia[fecha_clave]
        
        # Señal SHORT: Precio rompe máximo de M15 y luego cierra por debajo del mínimo de M1
        if high_price > rango['max']:
            # Obtener últimas velas M1
            idx_actual = self.data.index.get_loc(date)
            inicio = max(0, idx_actual - self.velas_m1)
            ultimas_velas_1M = self.data.iloc[inicio:idx_actual]
            
            if len(ultimas_velas_1M) > 0 and close_price < ultimas_velas_1M['low'].min():
                # Calcular SL como máximo desde las 20:00
                current_day = date.date()
                velas_desde_20 = self.data.loc[
                    (self.data.index.date == current_day) & 
                    (self.data.index.time >= time(20, 0)) & 
                    (self.data.index <= date)
                ]
                
                if len(velas_desde_20) > 0:
                    max_desde_20 = velas_desde_20['high'].max()
                    risk_amount = self.cash * self.risk
                    decimales = abs(int(round(-math.log10(self.decimal))))
                    
                    entry_price = round(close_price, decimales)
                    sl_price = round(max_desde_20, decimales) + self.decimal * 50
                    tp_price = round(entry_price - abs(entry_price - sl_price) * self.ratio, decimales)
                    
                    # Aplicar spread y slippage
                    spread = self.data['spread'].iloc[idx_actual] * self.decimal
                    slippage_value = max(self.data['slippage'].iloc[idx_actual], self.decimal)
                    entry_price += spread + slippage_value
                    entry_price = round(entry_price, decimales)
                    
                    position_size = self._calcular_tamaño_posicion(risk_amount, entry_price, sl_price)
                    
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
                        'Precio salida': None
                    }
        return None
    
    def _evaluar_señal_larga(self, date, close_price, low_price, high_price, fecha_clave):
        """Evalúa señal de compra (LONG)"""
        if fecha_clave not in self.rangos_por_dia:
            return None
            
        rango = self.rangos_por_dia[fecha_clave]
        
        # Señal LONG: Precio rompe mínimo de M15 y luego cierra por encima del máximo de M1
        if low_price < rango['min']:
            # Obtener últimas velas M1
            idx_actual = self.data.index.get_loc(date)
            inicio = max(0, idx_actual - self.velas_m1)
            ultimas_velas_1M = self.data.iloc[inicio:idx_actual]
            
            if len(ultimas_velas_1M) > 0 and close_price > ultimas_velas_1M['high'].max():
                # Calcular SL como mínimo desde las 20:00
                current_day = date.date()
                velas_desde_20 = self.data.loc[
                    (self.data.index.date == current_day) & 
                    (self.data.index.time >= time(20, 0)) & 
                    (self.data.index <= date)
                ]
                
                if len(velas_desde_20) > 0:
                    min_desde_20 = velas_desde_20['low'].min()
                    risk_amount = self.cash * self.risk
                    decimales = abs(int(round(-math.log10(self.decimal))))
                    
                    entry_price = round(close_price, decimales)
                    sl_price = round(min_desde_20, decimales) - self.decimal * 50
                    tp_price = round(entry_price + abs(entry_price - sl_price) * self.ratio, decimales)
                    
                    # Aplicar spread y slippage
                    spread = self.data['spread'].iloc[idx_actual] * self.decimal
                    slippage_value = max(self.data['slippage'].iloc[idx_actual], self.decimal)
                    entry_price -= spread + slippage_value  # Para long restamos
                    entry_price = round(entry_price, decimales)
                    
                    position_size = self._calcular_tamaño_posicion(risk_amount, entry_price, sl_price)
                    
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
                        'Precio salida': None
                    }
        return None
    
    def _cerrar_operaciones(self, date, high_price, low_price):
        """Cierra operaciones que alcanzan SL o TP"""
        operaciones_cerradas = []
        
        for operacion in self.open_trades[:]:
            cerrar_operacion = False
            precio_salida = None
            resultado = 0
            
            if operacion['Tipo'] == 'short':
                # SHORT: TP por debajo, SL por encima
                if low_price <= operacion['TP']:
                    # TP alcanzado
                    precio_salida = operacion['TP']
                    resultado = (operacion['Precio de entrada'] - precio_salida) * operacion['Cantidad'] * self.tamcontrato
                    cerrar_operacion = True
                elif high_price >= operacion['SL']:
                    # SL alcanzado
                    precio_salida = operacion['SL']
                    resultado = (operacion['Precio de entrada'] - precio_salida) * operacion['Cantidad'] * self.tamcontrato
                    cerrar_operacion = True
                    
            elif operacion['Tipo'] == 'long':
                # LONG: TP por encima, SL por debajo
                if high_price >= operacion['TP']:
                    # TP alcanzado
                    precio_salida = operacion['TP']
                    resultado = (precio_salida - operacion['Precio de entrada']) * operacion['Cantidad'] * self.tamcontrato
                    cerrar_operacion = True
                elif low_price <= operacion['SL']:
                    # SL alcanzado
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
        
        return operaciones_cerradas
    
    def run(self):
        """Ejecuta la estrategia completa"""
        print("Ejecutando estrategia ICT...")
        
        for i in range(1, len(self.data)):
            date = self.data.index[i]
            close_price = self.data['close'].iloc[i]
            low_price = self.data['low'].iloc[i]
            high_price = self.data['high'].iloc[i]
            
            # Cerrar operaciones existentes si alcanzan SL/TP
            self._cerrar_operaciones(date, high_price, low_price)
            
            # Verificar si es entre las 20 y las 22 y no hay operaciones abiertas
            hora_actual = date.time()
            if (time(20, 0) <= hora_actual < time(22, 0) and 
                len(self.open_trades) == 0):
                
                fecha_clave = date.date()
                
                # Verificar que no haya operación hoy
                operacion_hoy = any(op['Fecha de entrada'].date() == fecha_clave 
                                  for op in self.operations + self.open_trades)
                
                if not operacion_hoy:
                    # Evaluar señales SHORT y LONG
                    señal_corta = self._evaluar_señal_corta(date, close_price, low_price, high_price, fecha_clave)
                    señal_larga = self._evaluar_señal_larga(date, close_price, low_price, high_price, fecha_clave)
                    
                    # Priorizar una señal (en este caso, la primera que ocurra)
                    if señal_corta:
                        self.open_trades.append(señal_corta)
                    elif señal_larga:
                        self.open_trades.append(señal_larga)
        
        # Cerrar todas las operaciones abiertas al final del backtest
        for operacion in self.open_trades[:]:
            ultimo_precio = self.data['close'].iloc[-1]
            resultado = 0
            
            if operacion['Tipo'] == 'short':
                resultado = (operacion['Precio de entrada'] - ultimo_precio) * operacion['Cantidad'] * self.tamcontrato
            else:  # long
                resultado = (ultimo_precio - operacion['Precio de entrada']) * operacion['Cantidad'] * self.tamcontrato
            
            operacion['Fecha de salida'] = self.data.index[-1]
            operacion['Precio salida'] = ultimo_precio
            operacion['Resultado'] = resultado
            self.cash += resultado
            self.operations.append(operacion)
        
        self.open_trades.clear()
        
        return self.operations
    
    def get_results(self):
        """Obtiene resultados de la estrategia"""
        if not self.operations:
            return {
                'capital_inicial': self.initial_cash,
                'capital_final': self.cash,
                'total_operaciones': 0,
                'operaciones_ganadas': 0,
                'operaciones_perdidas': 0,
                'porcentaje_ganadas': 0,
                'profit_total': 0,
                'profit_percent': 0
            }
        
        operaciones_ganadas = sum(1 for op in self.operations if op['Resultado'] > 0)
        operaciones_perdidas = sum(1 for op in self.operations if op['Resultado'] <= 0)
        profit_total = self.cash - self.initial_cash
        profit_porcentaje = (profit_total / self.initial_cash) * 100
        
        return {
            'capital_inicial': self.initial_cash,
            'capital_final': self.cash,
            'total_operaciones': len(self.operations),
            'operaciones_ganadas': operaciones_ganadas,
            'operaciones_perdidas': operaciones_perdidas,
            'porcentaje_ganadas': (operaciones_ganadas / len(self.operations)) * 100,
            'profit_total': profit_total,
            'profit_percent': profit_porcentaje
        }