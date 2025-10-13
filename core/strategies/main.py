# main.py
from ict_money import StrategyICT
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
        self.ultima_vela = None
        self.operations = []  # Historial de operaciones
        self.open_trades = []  # Operaciones abiertas
        
        # Parámetros del símbolo
        self.decimal = 0.0001
        self.tamcontrato = 100000
        self.swap = 0
        
    def inicializar_mt5(self):
        """Inicializa la conexión con MetaTrader 5"""
        if not mt5.initialize():
            print("Error al inicializar MT5")
            return False
        
        # Verificar símbolo
        if not mt5.symbol_select(self.symbol, True):
            print(f"Error: Símbolo {self.symbol} no disponible")
            return False
            
        print(f"Bot inicializado para {self.symbol}")
        print(f"Capital inicial: ${self.initial_cash:,.2f}")
        print(f"Riesgo por operación: {self.risk*100}%")
        return True
    
    def obtener_datos_iniciales(self):
        """Obtiene datos históricos para inicializar la estrategia"""
        print("Obteniendo datos históricos para inicializar estrategia...")
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 10000)
        if rates is None:
            print("Error al obtener datos históricos")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        print(f"Datos históricos obtenidos: {len(df)} velas")
        return df
    
    def _calcular_tamaño_posicion(self, entry_price, sl_price):
        """Calcula el tamaño de posición basado en el capital dinámico"""
        risk_amount = self.cash * self.risk
        riesgo_por_contrato = abs(entry_price - sl_price) * self.tamcontrato
        
        if riesgo_por_contrato > 0:
            tamaño = (risk_amount / riesgo_por_contrato)
            # Ajustar a tamaño mínimo y máximo razonable
            tamaño = max(0.01, min(tamaño, self.cash * 0.1 / riesgo_por_contrato))
            return round(tamaño, 2)
        return 0.01
    
    def _evaluar_señal_ict(self, data_actual):
        """Evalúa señales ICT en tiempo real (versión simplificada)"""
        try:
            hora_actual = datetime.now().time()
            
            # Solo operar entre 20:00 y 22:00
            if not (20 <= datetime.now().hour < 22):
                return None
                
            # Obtener datos recientes para análisis
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 100)
            if rates is None:
                return None
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return None
                
            current_price = tick.bid
            current_high = df['high'].iloc[-1] if len(df) > 0 else current_price
            current_low = df['low'].iloc[-1] if len(df) > 0 else current_price
            
            # Aquí iría la lógica completa de detección de señales ICT
            # Por ahora, usemos una versión simplificada para demostración
            
            # Señal SHORT de ejemplo (debes implementar tu lógica ICT completa)
            if len(df) >= 30:
                # Ejemplo: Precio rompe máximo de últimas 15 velas y retrocede
                max_15_velas = df['high'].tail(15).max()
                min_30_velas = df['low'].tail(30).min()
                
                if current_high > max_15_velas and current_price < min_30_velas:
                    # Calcular SL y TP
                    sl_price = current_high + 0.0010  # SL por encima del máximo
                    tp_price = current_price - (sl_price - current_price) * self.ratio
                    
                    lotaje = self._calcular_tamaño_posicion(current_price, sl_price)
                    
                    return {
                        'tipo': 'SELL',
                        'entry': current_price,
                        'sl': sl_price,
                        'tp': tp_price,
                        'lotaje': lotaje,
                        'razon': 'Señal ICT SHORT'
                    }
            
            # Señal LONG de ejemplo
            if len(df) >= 30:
                min_15_velas = df['low'].tail(15).min()
                max_30_velas = df['high'].tail(30).max()
                
                if current_low < min_15_velas and current_price > max_30_velas:
                    # Calcular SL y TP
                    sl_price = current_low - 0.0010  # SL por debajo del mínimo
                    tp_price = current_price + (current_price - sl_price) * self.ratio
                    
                    lotaje = self._calcular_tamaño_posicion(current_price, sl_price)
                    
                    return {
                        'tipo': 'BUY', 
                        'entry': current_price,
                        'sl': sl_price,
                        'tp': tp_price,
                        'lotaje': lotaje,
                        'razon': 'Señal ICT LONG'
                    }
                    
            return None
            
        except Exception as e:
            print(f"Error en evaluación de señal: {e}")
            return None
    
    def ejecutar_operacion(self, señal):
        """Ejecuta una operación en MT5 con capital dinámico"""
        try:
            if señal['tipo'] == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(self.symbol).bid
            
            # Calcular lotaje dinámico basado en capital actual
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
                "comment": f"ICT Strategy - {señal['razon']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Error al abrir operación: {result.retcode}")
                return False
            
            # Registrar la operación
            operacion = {
                'ticket': result.order,
                'tipo': señal['tipo'],
                'precio_entrada': price,
                'sl': señal['sl'],
                'tp': señal['tp'],
                'lotaje': lotaje,
                'fecha_apertura': datetime.now(),
                'capital_antes': self.cash,
                'razon': señal['razon']
            }
            
            self.open_trades.append(operacion)
            
            print(f"✅ Operación {señal['tipo']} abierta:")
            print(f"   - Precio: {price:.5f}")
            print(f"   - SL: {señal['sl']:.5f}")
            print(f"   - TP: {señal['tp']:.5f}") 
            print(f"   - Lotaje: {lotaje:.2f} (Capital: ${self.cash:,.2f})")
            print(f"   - Razón: {señal['razon']}")
            
            return True
            
        except Exception as e:
            print(f"Error ejecutando operación: {e}")
            return False
    
    def actualizar_capital(self):
        """Actualiza el capital basado en operaciones cerradas"""
        try:
            # Obtener posiciones actuales
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                positions = []
            
            # Buscar operaciones cerradas
            for operacion in self.open_trades[:]:
                operacion_cerrada = True
                
                for pos in positions:
                    if pos.ticket == operacion['ticket']:
                        operacion_cerrada = False
                        break
                
                if operacion_cerrada:
                    # Calcular resultado (simplificado)
                    # En una implementación real, obtendrías el resultado real de MT5
                    tick_actual = mt5.symbol_info_tick(self.symbol)
                    if tick_actual:
                        if operacion['tipo'] == 'BUY':
                            resultado = (tick_actual.bid - operacion['precio_entrada']) * operacion['lotaje'] * self.tamcontrato
                        else:
                            resultado = (operacion['precio_entrada'] - tick_actual.bid) * operacion['lotaje'] * self.tamcontrato
                        
                        self.cash += resultado
                        
                        print(f"🔒 Operación {operacion['tipo']} cerrada:")
                        print(f"   - Resultado: ${resultado:,.2f}")
                        print(f"   - Nuevo capital: ${self.cash:,.2f}")
                        print(f"   - Capital inicial: ${self.initial_cash:,.2f}")
                        print(f"   - Profit acumulado: ${self.cash - self.initial_cash:,.2f}")
                        
                        # Guardar en historial
                        operacion['fecha_cierre'] = datetime.now()
                        operacion['resultado'] = resultado
                        operacion['capital_despues'] = self.cash
                        self.operations.append(operacion)
                        self.open_trades.remove(operacion)
            
            # Actualizar estado de operación abierta
            self.operacion_abierta = len(self.open_trades) > 0
            
        except Exception as e:
            print(f"Error actualizando capital: {e}")
    
    def mostrar_estado(self):
        """Muestra el estado actual del bot"""
        profit_total = self.cash - self.initial_cash
        profit_porcentaje = (profit_total / self.initial_cash) * 100
        
        print(f"\n📊 ESTADO BOT - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Capital actual: ${self.cash:,.2f}")
        print(f"   Capital inicial: ${self.initial_cash:,.2f}")
        print(f"   Profit total: ${profit_total:,.2f} ({profit_porcentaje:+.2f}%)")
        print(f"   Operaciones abiertas: {len(self.open_trades)}")
        print(f"   Operaciones históricas: {len(self.operations)}")
        
        if self.open_trades:
            for op in self.open_trades:
                print(f"   - {op['tipo']} | Lotes: {op['lotaje']:.2f} | Entrada: {op['precio_entrada']:.5f}")
    
    def run(self):
        """Ejecuta el bot de trading con capital dinámico"""
        if not self.inicializar_mt5():
            return
        
        try:
            # Obtener datos iniciales
            data = self.obtener_datos_iniciales()
            if data is None:
                print("No se pudieron obtener datos iniciales, continuando...")
            
            print("\n🤖 BOT ICT INICIADO - CAPITAL DINÁMICO")
            print("   Presiona Ctrl+C para detener")
            print("=" * 50)
            
            # Bucle principal
            while True:
                try:
                    # Actualizar capital y operaciones
                    self.actualizar_capital()
                    
                    # Mostrar estado cada 30 segundos
                    if datetime.now().second % 30 == 0:
                        self.mostrar_estado()
                    
                    # Buscar señales solo si no hay operación abierta
                    if not self.operacion_abierta:
                        señal = self._evaluar_señal_ict(data)
                        if señal:
                            print(f"🎯 Señal detectada: {señal['razon']}")
                            self.ejecutar_operacion(señal)
                    
                    # Esperar 5 segundos antes de la siguiente verificación
                    time.sleep(5)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Deteniendo bot...")
                    break
                except Exception as e:
                    print(f"⚠️ Error en bucle principal: {e}")
                    time.sleep(10)
                    
        finally:
            self.mostrar_estado()
            mt5.shutdown()
            print("🔌 Conexión con MT5 cerrada")

def main():
    # Configuración del bot con capital dinámico
    SYMBOL = "EURUSDm"  # Asegúrate de que este símbolo existe en tu MT5
    
    # Crear y ejecutar bot con capital dinámico
    bot = TradingBot(
        symbol=SYMBOL,
        risk=0.01,          # 1% de riesgo por operación
        ratio=2,            # Ratio TP/SL 2:1
        initial_cash=10000  # Capital inicial
    )
    
    bot.run()

if __name__ == "__main__":
    main()