import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime, timedelta
import math

class TradingBot:
    def __init__(self, symbol, risk=0.01, ratio=2, initial_cash=10000):
        self.symbol = symbol
        self.risk = risk
        self.ratio = ratio
        self.initial_cash = initial_cash
        self.cash = initial_cash  # Capital dinámico
        self.operacion_abierta = False
        self.operations = []
        self.open_trades = []
        
        # Parámetros del símbolo
        self.decimal = 0.0001
        self.tamcontrato = 100000
        self.swap = 0
        
    def inicializar_mt5(self):
        """Inicializa la conexión con MetaTrader 5"""
        if not mt5.initialize():
            print("Error al inicializar MT5")
            return False
        
        if not mt5.symbol_select(self.symbol, True):
            print(f"Error: Símbolo {self.symbol} no disponible")
            return False
            
        print(f"Bot inicializado para {self.symbol}")
        print(f"Capital inicial: ${self.initial_cash:,.2f}")
        print(f"Riesgo por operación: {self.risk*100}% (Dinámico)")
        return True

    def obtener_capital_real(self):
        """Obtiene el capital REAL de la cuenta MT5"""
        try:
            account_info = mt5.account_info()
            if account_info:
                # Usar el balance real de la cuenta
                capital_real = account_info.balance
                print(f"💰 Capital real de la cuenta: ${capital_real:,.2f}")
                return capital_real
            else:
                print("⚠️ No se pudo obtener información de la cuenta, usando capital configurado")
                return self.cash
        except Exception as e:
            print(f"Error obteniendo capital real: {e}")
            return self.cash

    def obtener_datos_reales(self, velas=100):
        """Obtiene datos REALES de MT5 para análisis"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, velas)
            if rates is None:
                print("Error al obtener datos reales")
                return None
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Calcular ATR para slippage real
            df['ATR'] = self.calcular_atr(df, period=14)
            df['slippage'] = df['ATR'] * 0.003
            
            return df
        except Exception as e:
            print(f"Error obteniendo datos reales: {e}")
            return None

    def calcular_atr(self, df, period=14):
        """Calcula el ATR para datos reales"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr = np.maximum(high - low, 
                           np.maximum(abs(high - close.shift()), 
                                     abs(low - close.shift())))
            atr = tr.rolling(window=period).mean()
            return atr
        except Exception as e:
            print(f"Error calculando ATR: {e}")
            return pd.Series([0.0005] * len(df), index=df.index)

    def _calcular_tamaño_posicion(self, entry_price, sl_price):
        """Calcula el tamaño de posición basado en el capital REAL"""
        # Usar capital real de la cuenta
        capital_real = self.obtener_capital_real()
        risk_amount = capital_real * self.risk
        riesgo_por_contrato = abs(entry_price - sl_price) * self.tamcontrato
        
        if riesgo_por_contrato > 0:
            tamaño = (risk_amount / riesgo_por_contrato)
            tamaño = max(0.01, min(tamaño, capital_real * 0.1 / riesgo_por_contrato))
            return round(tamaño, 2)
        return 0.01

    def _calcular_rangos_m15_reales(self, data):
        """Calcula rangos M15 con datos reales"""
        try:
            # Resample a 15 minutos con datos reales
            data_m15 = data.resample('15min').agg({
                'open': 'first',
                'high': 'max', 
                'low': 'min',
                'close': 'last'
            }).dropna()
            
            # Filtrar velas antes de las 20:00
            from datetime import time
            data_15M_filtrado = data_m15[data_m15.index.time < time(20, 0)]
            
            # Agrupar por día
            grupos_por_dia = data_15M_filtrado.groupby(data_15M_filtrado.index.date)
            
            rangos_por_dia = {}
            for fecha, grupo in grupos_por_dia:
                if len(grupo) >= 3:  # Últimas 3 velas M15
                    ultimas_velas = grupo.tail(3)
                    minimo = ultimas_velas['low'].min()
                    maximo = ultimas_velas['high'].max()
                    rangos_por_dia[fecha] = {'min': minimo, 'max': maximo}
            
            return rangos_por_dia
        except Exception as e:
            print(f"Error calculando rangos M15: {e}")
            return {}

    def _evaluar_señal_ict_real(self):
        """Evalúa señales ICT con datos REALES de MT5"""
        try:
            hora_actual = datetime.now().time()
            
            # Solo operar entre 20:00 y 22:00
            if not (20 <= datetime.now().hour < 22):
                return None
                
            # Obtener datos REALES
            data = self.obtener_datos_reales(velas=500)  # Más datos para mejor análisis
            if data is None or len(data) < 30:
                return None
                
            # Obtener precio actual REAL
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return None
                
            current_price = tick.bid
            current_high = data['high'].iloc[-1]
            current_low = data['low'].iloc[-1]
            
            # Calcular rangos M15 con datos reales
            rangos_por_dia = self._calcular_rangos_m15_reales(data)
            fecha_hoy = datetime.now().date()
            
            if fecha_hoy not in rangos_por_dia:
                return None
                
            rango = rangos_por_dia[fecha_hoy]
            
            # Señal SHORT: Precio rompe máximo de M15 y luego cierra por debajo del mínimo de M1
            if current_high > rango['max']:
                # Obtener últimas velas M1
                ultimas_velas_1M = data.tail(30)
                
                if len(ultimas_velas_1M) > 0 and current_price < ultimas_velas_1M['low'].min():
                    # Calcular SL como máximo desde las 20:00
                    velas_desde_20 = data[data.index.time >= time(20, 0)]
                    if len(velas_desde_20) > 0:
                        max_desde_20 = velas_desde_20['high'].max()
                        
                        entry_price = current_price
                        sl_price = max_desde_20 + self.decimal * 50
                        tp_price = entry_price - abs(entry_price - sl_price) * self.ratio
                        
                        # Aplicar spread y slippage real
                        spread = data['spread'].iloc[-1] * self.decimal if 'spread' in data.columns else 0.0001
                        slippage_value = data['slippage'].iloc[-1] if 'slippage' in data.columns else 0.0001
                        entry_price += spread + slippage_value
                        
                        position_size = self._calcular_tamaño_posicion(entry_price, sl_price)
                        
                        return {
                            'tipo': 'SELL',
                            'entry': entry_price,
                            'sl': sl_price,
                            'tp': tp_price,
                            'lotaje': position_size,
                            'razon': 'ICT SHORT - Breakout M15 + Retest M1'
                        }
            
            # Señal LONG: Precio rompe mínimo de M15 y luego cierra por encima del máximo de M1
            if current_low < rango['min']:
                # Obtener últimas velas M1
                ultimas_velas_1M = data.tail(30)
                
                if len(ultimas_velas_1M) > 0 and current_price > ultimas_velas_1M['high'].max():
                    # Calcular SL como mínimo desde las 20:00
                    velas_desde_20 = data[data.index.time >= time(20, 0)]
                    if len(velas_desde_20) > 0:
                        min_desde_20 = velas_desde_20['low'].min()
                        
                        entry_price = current_price
                        sl_price = min_desde_20 - self.decimal * 50
                        tp_price = entry_price + abs(entry_price - sl_price) * self.ratio
                        
                        # Aplicar spread y slippage real
                        spread = data['spread'].iloc[-1] * self.decimal if 'spread' in data.columns else 0.0001
                        slippage_value = data['slippage'].iloc[-1] if 'slippage' in data.columns else 0.0001
                        entry_price -= spread + slippage_value
                        
                        position_size = self._calcular_tamaño_posicion(entry_price, sl_price)
                        
                        return {
                            'tipo': 'BUY',
                            'entry': entry_price,
                            'sl': sl_price,
                            'tp': tp_price,
                            'lotaje': position_size,
                            'razon': 'ICT LONG - Breakdown M15 + Retest M1'
                        }
            
            return None
            
        except Exception as e:
            print(f"Error en evaluación de señal real: {e}")
            return None

    def verificar_operaciones_abiertas_reales(self):
        """Verifica operaciones REALES abiertas en MT5"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                return 0
            return len(positions)
        except Exception as e:
            print(f"Error verificando operaciones reales: {e}")
            return 0

    def ejecutar_operacion_real(self, señal):
        """Ejecuta una operación REAL en MT5"""
        try:
            # Verificar que no haya operaciones abiertas REALES
            operaciones_abiertas = self.verificar_operaciones_abiertas_reales()
            if operaciones_abiertas > 0:
                print(f"⚠️ Ya hay {operaciones_abiertas} operación(es) abierta(s), no se abre nueva")
                return False

            if señal['tipo'] == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(self.symbol).bid
            
            lotaje = señal['lotaje']
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lotaje,
                "type": order_type,
                "price": price,
                "sl": señal['sl'],
                "tp": señal['tp'],
                "deviation": 20,
                "magic": 234000,
                "comment": f"ICT Dynamic - {señal['razon']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ Error al abrir operación: {result.retcode}")
                print(f"   Detalles: {result}")
                return False
            
            # Actualizar capital real después de abrir operación
            capital_actual = self.obtener_capital_real()
            
            operacion = {
                'ticket': result.order,
                'tipo': señal['tipo'],
                'precio_entrada': price,
                'sl': señal['sl'],
                'tp': señal['tp'],
                'lotaje': lotaje,
                'fecha_apertura': datetime.now(),
                'capital_antes': capital_actual,
                'razon': señal['razon']
            }
            
            self.open_trades.append(operacion)
            
            print(f"✅ Operación REAL {señal['tipo']} abierta:")
            print(f"   - Ticket: {result.order}")
            print(f"   - Precio: {price:.5f}")
            print(f"   - SL: {señal['sl']:.5f}")
            print(f"   - TP: {señal['tp']:.5f}") 
            print(f"   - Lotaje: {lotaje:.2f}")
            print(f"   - Capital real: ${capital_actual:,.2f}")
            print(f"   - Razón: {señal['razon']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error ejecutando operación real: {e}")
            return False

    def actualizar_estado_operaciones_reales(self):
        """Actualiza el estado de las operaciones REALES"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                positions = []
            
            current_tickets = [pos.ticket for pos in positions]
            
            # Verificar operaciones cerradas
            for operacion in self.open_trades[:]:
                if operacion['ticket'] not in current_tickets:
                    # Operación cerrada, obtener resultado real
                    history_orders = mt5.history_orders_get(
                        datetime.now() - timedelta(hours=1), 
                        datetime.now()
                    )
                    
                    if history_orders:
                        for order in history_orders:
                            if order.ticket == operacion['ticket']:
                                resultado = order.profit
                                break
                        else:
                            # Si no encontramos en history, estimamos
                            tick_actual = mt5.symbol_info_tick(self.symbol)
                            if tick_actual:
                                if operacion['tipo'] == 'BUY':
                                    resultado = (tick_actual.bid - operacion['precio_entrada']) * operacion['lotaje'] * self.tamcontrato
                                else:
                                    resultado = (operacion['precio_entrada'] - tick_actual.bid) * operacion['lotaje'] * self.tamcontrato
                            else:
                                resultado = 0
                    else:
                        resultado = 0
                    
                    # Actualizar capital REAL
                    capital_actual = self.obtener_capital_real()
                    
                    print(f"🔒 Operación REAL {operacion['tipo']} cerrada:")
                    print(f"   - Resultado: ${resultado:,.2f}")
                    print(f"   - Capital real actual: ${capital_actual:,.2f}")
                    
                    operacion['fecha_cierre'] = datetime.now()
                    operacion['resultado'] = resultado
                    operacion['capital_despues'] = capital_actual
                    self.operations.append(operacion)
                    self.open_trades.remove(operacion)
            
            # Actualizar estado de operación abierta
            self.operacion_abierta = len(positions) > 0
            
        except Exception as e:
            print(f"Error actualizando estado operaciones reales: {e}")

    def mostrar_estado_real(self):
        """Muestra el estado REAL del bot"""
        try:
            capital_real = self.obtener_capital_real()
            profit_total = capital_real - self.initial_cash
            profit_porcentaje = (profit_total / self.initial_cash) * 100
            
            operaciones_abiertas = self.verificar_operaciones_abiertas_reales()
            
            print(f"\n📊 ESTADO REAL BOT - {datetime.now().strftime('%H:%M:%S')}")
            print(f"   💰 Capital REAL: ${capital_real:,.2f}")
            print(f"   📈 Capital inicial: ${self.initial_cash:,.2f}")
            print(f"   💵 Profit total: ${profit_total:,.2f} ({profit_porcentaje:+.2f}%)")
            print(f"   🔄 Operaciones REALES abiertas: {operaciones_abiertas}")
            print(f"   📋 Operaciones históricas: {len(self.operations)}")
            
            if operaciones_abiertas > 0:
                positions = mt5.positions_get(symbol=self.symbol)
                for pos in positions:
                    tipo = "BUY" if pos.type == 0 else "SELL"
                    print(f"   - {tipo} | Lotes: {pos.volume:.2f} | Entrada: {pos.price_open:.5f} | Profit: ${pos.profit:.2f}")
        
        except Exception as e:
            print(f"Error mostrando estado real: {e}")

    def run(self):
        """Ejecuta el bot de trading con datos REALES"""
        if not self.inicializar_mt5():
            return
        
        try:
            # Mostrar información inicial REAL
            capital_inicial_real = self.obtener_capital_real()
            print(f"\n🎯 BOT ICT INICIADO - DATOS REALES")
            print(f"   Capital inicial REAL: ${capital_inicial_real:,.2f}")
            print(f"   Símbolo: {self.symbol}")
            print(f"   Riesgo: {self.risk*100}% por operación")
            print(f"   Ratio TP/SL: {self.ratio}:1")
            print("   Presiona Ctrl+C para detener")
            print("=" * 60)
            
            while True:
                try:
                    # Actualizar estado con datos REALES
                    self.actualizar_estado_operaciones_reales()
                    
                    # Mostrar estado REAL cada 30 segundos
                    if datetime.now().second % 30 == 0:
                        self.mostrar_estado_real()
                    
                    # Buscar señales solo si no hay operación REAL abierta
                    operaciones_abiertas = self.verificar_operaciones_abiertas_reales()
                    if operaciones_abiertas == 0:
                        señal = self._evaluar_señal_ict_real()
                        if señal:
                            print(f"🎯 Señal ICT detectada con datos REALES")
                            self.ejecutar_operacion_real(señal)
                    else:
                        # Pequeña pausa si hay operación abierta
                        time.sleep(2)
                    
                    time.sleep(5)  # Espera entre verificaciones
                    
                except KeyboardInterrupt:
                    print("\n🛑 Deteniendo bot...")
                    break
                except Exception as e:
                    print(f"⚠️ Error en bucle principal: {e}")
                    time.sleep(10)
                    
        finally:
            self.mostrar_estado_real()
            mt5.shutdown()
            print("🔌 Conexión con MT5 cerrada")

# Agregar import necesario para numpy
import numpy as np

def main():
    SYMBOL = "EURUSDm"  # Asegúrate que este símbolo existe en tu MT5
    
    bot = TradingBot(
        symbol=SYMBOL,
        risk=0.01,      # 1% de riesgo por operación
        ratio=3,        # Ratio TP/SL 2:1
        initial_cash=10000
    )
    
    bot.run()

if __name__ == "__main__":
    main()