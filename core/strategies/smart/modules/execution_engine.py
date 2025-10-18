# execution_engine.py - Motor de ejecución de órdenes MT5
import MetaTrader5 as mt5
import pandas as pd
from typing import Dict, Optional, Tuple
import logging
import time
from datetime import datetime

class ExecutionEngine:
    def _init_(self, order_config: Dict):
        self.order_config = order_config
        self.magic_number = 202410  # Número mágico para identificar nuestras órdenes
        self.logger = logging.getLogger(_name_)
        self.max_retries = 3
    
    def execute_trade(self, signal: Dict, symbol: str, 
                     balance: float, risk_manager) -> Dict:
        """Ejecutar trade basado en señal"""
        
        # Calcular niveles de SL/TP
        sl_price, tp_price = self.calculate_sl_tp(signal, symbol)
        if not sl_price or not tp_price:
            self.logger.error("No se pudieron calcular SL/TP")
            return None
        
        # Calcular tamaño de posición
        stop_pips = self.calculate_stop_pips(signal['entry_price'], sl_price, symbol)
        lot_size = risk_manager.calculate_position_size(balance, stop_pips, symbol)
        
        if lot_size <= 0:
            self.logger.error(f"Tamaño de lote inválido: {lot_size}")
            return None
        
        # Crear request de orden
        order_type = mt5.ORDER_TYPE_BUY if signal['direction'] == 'bullish' else mt5.ORDER_TYPE_SELL
        order_request = self.create_order_request(
            symbol, order_type, lot_size, signal['entry_price'], 
            sl_price, tp_price
        )
        
        # Validar y enviar orden
        return self.send_order(order_request, symbol)
    
    def calculate_sl_tp(self, signal: Dict, symbol: str) -> Tuple[float, float]:
        """Calcular Stop Loss y Take Profit basado en la configuración"""
        entry_price = signal['entry_price']
        direction = signal['direction']
        default_stop_pips = self.order_config['default_stop_pips']
        rr_target = self.order_config['rr_target']
        
        # Obtener información del símbolo para pip size
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            self.logger.error(f"No se pudo obtener info del símbolo: {symbol}")
            return None, None
        
        pip_size = symbol_info.point * 10  # Para la mayoría de pares Forex
        
        # Calcular SL basado en el patrón y dirección
        if direction == 'bullish':
            sl_price = entry_price - (default_stop_pips * pip_size)
            tp_price = entry_price + (default_stop_pips * rr_target * pip_size)
        else:  # bearish
            sl_price = entry_price + (default_stop_pips * pip_size)
            tp_price = entry_price - (default_stop_pips * rr_target * pip_size)
        
        # Ajustar SL si estamos usando un Order Block o zona de liquidez
        sl_price = self.adjust_sl_for_level(sl_price, signal, direction, pip_size)
        
        return sl_price, tp_price
    
    def adjust_sl_for_level(self, sl_price: float, signal: Dict, 
                          direction: str, pip_size: float) -> float:
        """Ajustar SL para respetar niveles institucionales"""
        # En una implementación completa, aquí se ajustaría el SL
        # para colocarlo más allá del Order Block o zona de liquidez
        adjustment_pips = 2  # 2 pips más allá del nivel
        
        if direction == 'bullish':
            return sl_price - (adjustment_pips * pip_size)
        else:
            return sl_price + (adjustment_pips * pip_size)
    
    def calculate_stop_pips(self, entry_price: float, sl_price: float, symbol: str) -> float:
        """Calcular distancia del stop en pips"""
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return self.order_config['default_stop_pips']
        
        pip_size = symbol_info.point * 10
        stop_distance = abs(entry_price - sl_price)
        stop_pips = stop_distance / pip_size
        
        return stop_pips
    
    def create_order_request(self, symbol: str, order_type: int, lot_size: float,
                           entry_price: float, sl_price: float, tp_price: float) -> Dict:
        """Crear diccionario de request para MT5"""
        
        # Obtener precio actual
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            self.logger.error(f"No se pudo obtener tick para {symbol}")
            return None
        
        # Determinar precio de ejecución
        if order_type == mt5.ORDER_TYPE_BUY:
            execution_price = tick.ask
        else:
            execution_price = tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": execution_price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": self.order_config['max_slippage_pips'] * 10,  # Puntos
            "magic": self.magic_number,
            "comment": f"Estoico-SMT-{order_type}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC  # Immediate or Cancel
        }
        
        return request
    
    def send_order(self, order_request: Dict, symbol: str) -> Dict:
        """Enviar orden a MT5 con reintentos"""
        
        if not order_request:
            return {'success': False, 'error': 'Order request inválido'}
        
        for attempt in range(self.max_retries):
            try:
                # Validar orden primero (opcional)
                validation_result = mt5.order_check(order_request)
                if validation_result is not None:
                    if validation_result.retcode != mt5.TRADE_RETCODE_DONE:
                        self.logger.warning(f"Validación fallida: {validation_result.retcode}")
                        time.sleep(1)
                        continue
                
                # Enviar orden
                result = mt5.order_send(order_request)
                
                if result is None:
                    self.logger.error("Resultado de orden es None")
                    time.sleep(1)
                    continue
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    self.logger.info(f"Orden ejecutada exitosamente: {result.order}")
                    return {
                        'success': True,
                        'order_id': result.order,
                        'volume': result.volume,
                        'price': result.price,
                        'sl': result.sl,
                        'tp': result.tp,
                        'comment': result.comment,
                        'retcode': result.retcode
                    }
                else:
                    self.logger.warning(f"Intento {attempt + 1} fallido: {result.retcode}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Error enviando orden: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
        
        return {
            'success': False, 
            'error': f'Todos los intentos fallados para {symbol}',
            'retcode': getattr(result, 'retcode', 'UNKNOWN') if 'result' in locals() else 'NO_RESPONSE'
        }
    
    def close_position(self, position_id: int, symbol: str) -> Dict:
        """Cerrar posición existente"""
        position = mt5.positions_get(ticket=position_id)
        if not position:
            return {'success': False, 'error': 'Posición no encontrada'}
        
        position = position[0]
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {'success': False, 'error': 'No se pudo obtener tick'}
        
        close_price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position_id,
            "symbol": symbol,
            "volume": position.volume,
            "type": order_type,
            "price": close_price,
            "deviation": self.order_config['max_slippage_pips'] * 10,
            "magic": self.magic_number,
            "comment": "Estoico-CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        
        return self.send_order(close_request, symbol)
    
    def get_open_positions(self, symbol: str = None) -> list:
        """Obtener posiciones abiertas"""
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            return []
        
        return [
            {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == 0 else 'SELL',
                'volume': pos.volume,
                'open_price': pos.price_open,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'magic': pos.magic
            }
            for pos in positions if pos.magic == self.magic_number
        ]
    
    def modify_position(self, position_id: int, new_sl: float = None, 
                       new_tp: float = None) -> Dict:
        """Modificar SL/TP de posición existente"""
        position = mt5.positions_get(ticket=position_id)
        if not position:
            return {'success': False, 'error': 'Posición no encontrada'}
        
        position = position[0]
        
        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position_id,
            "symbol": position.symbol,
            "sl": new_sl if new_sl is not None else position.sl,
            "tp": new_tp if new_tp is not None else position.tp,
            "magic": self.magic_number,
            "comment": f"Estoico-MODIFY-{datetime.now().strftime('%H:%M')}"
        }
        
        result = mt5.order_send(modify_request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return {'success': True, 'message': 'Posición modificada exitosamente'}
        else:
            return {
                'success': False, 
                'error': f'Error modificando posición: {getattr(result, "retcode", "UNKNOWN")}'
            }