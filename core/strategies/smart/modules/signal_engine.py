# signal_engine.py - Motor de señales SMC completo
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import logging

class SignalEngine:
    def _init_(self, timeframe_config: Dict):
        self.structure_tf = timeframe_config['structure']
        self.execution_tf = timeframe_config['execution']
        self.logger = logging.getLogger(_name_)
    
    def analyze(self, m15_data: pd.DataFrame, m5_data: pd.DataFrame, 
                m1_data: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """Análisis principal combinando conceptos SMC"""
        
        if len(m15_data) < 20 or len(m5_data) < 10:
            return None
        
        # 1. Dirección institucional desde M15
        institutional_bias = self.get_institutional_bias(m15_data)
        if not institutional_bias:
            return None
        
        # 2. Identificar Order Blocks y zonas de liquidez
        order_blocks = self.detect_order_blocks(m15_data)
        liquidity_zones = self.find_liquidity_zones(m15_data)
        
        # 3. Verificar condiciones de entrada en timeframes menores
        entry_signal = self.check_entry_conditions(
            m5_data, m1_data, order_blocks, liquidity_zones, institutional_bias
        )
        
        return entry_signal
    
    def detect_order_blocks(self, data: pd.DataFrame) -> list:
        """Detectar Order Blocks basado en principios SMC"""
        ob_blocks = []
        
        for i in range(2, len(data)-1):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            prev_prev = data.iloc[i-2]
            next_candle = data.iloc[i+1]
            
            # OB Bajista: Vela bajista antes de impulso alcista
            if (prev_prev['close'] < prev_prev['open'] and 
                current['close'] > current['open'] and 
                current['close'] > prev_prev['high'] and
                abs(prev_prev['close'] - prev_prev['open']) > (prev_prev['high'] - prev_prev['low']) * 0.6):
                
                ob_blocks.append({
                    'type': 'bearish',
                    'high': prev_prev['high'],
                    'low': prev_prev['low'],
                    'open': prev_prev['open'],
                    'close': prev_prev['close'],
                    'timestamp': prev_prev['time'],
                    'strength': abs(prev_prev['close'] - prev_prev['open']) / (prev_prev['high'] - prev_prev['low'])
                })
            
            # OB Alcista: Vela alcista antes de impulso bajista
            elif (prev_prev['close'] > prev_prev['open'] and 
                  current['close'] < current['open'] and 
                  current['close'] < prev_prev['low'] and
                  abs(prev_prev['close'] - prev_prev['open']) > (prev_prev['high'] - prev_prev['low']) * 0.6):
                
                ob_blocks.append({
                    'type': 'bullish',
                    'high': prev_prev['high'],
                    'low': prev_prev['low'],
                    'open': prev_prev['open'],
                    'close': prev_prev['close'],
                    'timestamp': prev_prev['time'],
                    'strength': abs(prev_prev['close'] - prev_prev['open']) / (prev_prev['high'] - prev_prev['low'])
                })
        
        return ob_blocks[-5:]  # Últimos 5 OB
    
    def find_liquidity_zones(self, data: pd.DataFrame, window: int = 20) -> List[Dict]:
        """
        Detectar zonas de liquidez (Equal Highs/Equal Lows)
        basado en máximos y mínimos similares
        """
        liquidity_zones = []
        
        if len(data) < window:
            return liquidity_zones
        
        # Detectar Equal Highs (múltiples máximos similares)
        for i in range(window, len(data)):
            current_high = data['high'].iloc[i]
            
            # Buscar máximos similares en la ventana lookback
            lookback_highs = data['high'].iloc[i-window:i]
            similar_highs = lookback_highs[
                (lookback_highs >= current_high * 0.999) & 
                (lookback_highs <= current_high * 1.001)
            ]
            
            if len(similar_highs) >= 2:  # Al menos 2 máximos similares
                zone = {
                    'type': 'equal_high',
                    'price': current_high,
                    'strength': len(similar_highs),
                    'timestamp': data['time'].iloc[i],
                    'touches': len(similar_highs)
                }
                # Evitar duplicados
                if not any(abs(z['price'] - zone['price']) < 0.0001 for z in liquidity_zones):
                    liquidity_zones.append(zone)
        
        # Detectar Equal Lows (múltiples mínimos similares)
        for i in range(window, len(data)):
            current_low = data['low'].iloc[i]
            
            # Buscar mínimos similares en la ventana lookback
            lookback_lows = data['low'].iloc[i-window:i]
            similar_lows = lookback_lows[
                (lookback_lows >= current_low * 0.999) & 
                (lookback_lows <= current_low * 1.001)
            ]
            
            if len(similar_lows) >= 2:  # Al menos 2 mínimos similares
                zone = {
                    'type': 'equal_low',
                    'price': current_low,
                    'strength': len(similar_lows),
                    'timestamp': data['time'].iloc[i],
                    'touches': len(similar_lows)
                }
                # Evitar duplicados
                if not any(abs(z['price'] - zone['price']) < 0.0001 for z in liquidity_zones):
                    liquidity_zones.append(zone)
        
        return liquidity_zones
    
    def get_institutional_bias(self, data: pd.DataFrame) -> str:
        """Determinar sesgo del mercado usando BOS/CHOCH"""
        if len(data) < 10:
            return None
        
        # Calcular ATR para tolerancias dinámicas
        atr = self.calculate_atr(data, period=14)
        current_atr = atr.iloc[-1] if len(atr) > 0 else 0.001
        
        # Detectar BOS (Break of Structure)
        recent_highs = data['high'].tail(5)
        recent_lows = data['low'].tail(5)
        
        # BOS Alcista: Máximo más alto y mínimo más alto
        bos_bullish = (recent_highs.iloc[-1] > recent_highs.iloc[-2] + current_atr * 0.5 and 
                      recent_lows.iloc[-1] > recent_lows.iloc[-2] + current_atr * 0.3)
        
        # BOS Bajista: Mínimo más bajo y máximo más bajo  
        bos_bearish = (recent_lows.iloc[-1] < recent_lows.iloc[-2] - current_atr * 0.5 and 
                      recent_highs.iloc[-1] < recent_highs.iloc[-2] - current_atr * 0.3)
        
        # Detectar CHOCH (Change of Character)
        choch_bullish = self.detect_choch_bullish(data, current_atr)
        choch_bearish = self.detect_choch_bearish(data, current_atr)
        
        if bos_bullish or choch_bullish:
            return "bullish"
        elif bos_bearish or choch_bearish:
            return "bearish"
        
        return None
    
    def detect_choch_bullish(self, data: pd.DataFrame, atr: float) -> bool:
        """Detectar CHOCH alcista (ruptura de estructura bajista)"""
        if len(data) < 10:
            return False
        
        # Ruptura de máximo anterior después de una secuencia bajista
        current_high = data['high'].iloc[-1]
        previous_high = data['high'].iloc[-2]
        swing_high = data['high'].tail(10).max()
        
        return (current_high > previous_high + atr * 0.5 and 
                current_high > swing_high)
    
    def detect_choch_bearish(self, data: pd.DataFrame, atr: float) -> bool:
        """Detectar CHOCH bajista (ruptura de estructura alcista)"""
        if len(data) < 10:
            return False
        
        # Ruptura de mínimo anterior después de una secuencia alcista
        current_low = data['low'].iloc[-1]
        previous_low = data['low'].iloc[-2]
        swing_low = data['low'].tail(10).min()
        
        return (current_low < previous_low - atr * 0.5 and 
                current_low < swing_low)
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcular Average True Range"""
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def check_entry_conditions(self, m5_data: pd.DataFrame, m1_data: pd.DataFrame,
                             order_blocks: List, liquidity_zones: List, 
                             bias: str) -> Optional[Dict]:
        """Verificar condiciones de entrada en timeframe de ejecución"""
        
        if len(m5_data) < 3 or len(m1_data) < 2:
            return None
        
        current_m5 = m5_data.iloc[-1]
        previous_m5 = m5_data.iloc[-2]
        current_m1 = m1_data.iloc[-1]
        
        # Verificar si estamos cerca de un Order Block o zona de liquidez
        near_ob = self.is_near_order_block(current_m5, order_blocks, bias)
        near_liquidity = self.is_near_liquidity_zone(current_m5, liquidity_zones, bias)
        
        if not (near_ob or near_liquidity):
            return None
        
        # Buscar patrón de vela de rechazo
        rejection_pattern = self.detect_rejection_pattern(current_m5, previous_m5, bias)
        
        if rejection_pattern:
            return {
                'direction': bias,
                'entry_price': current_m5['close'],
                'pattern': rejection_pattern,
                'type': 'order_block' if near_ob else 'liquidity_sweep',
                'timestamp': current_m5['time'],
                'confidence': self.calculate_confidence(current_m5, rejection_pattern, bias)
            }
        
        return None
    
    def is_near_order_block(self, current_candle: pd.Series, order_blocks: List, bias: str) -> bool:
        """Verificar si el precio está cerca de un Order Block relevante"""
        if not order_blocks:
            return False
        
        current_price = current_candle['close']
        relevant_obs = [ob for ob in order_blocks if ob['type'] != bias]  # OBs contrarios
        
        for ob in relevant_obs[-3:]:  # Últimos 3 OBs relevantes
            ob_range = ob['low'] if bias == 'bullish' else ob['high']
            price_diff = abs(current_price - ob_range)
            
            if price_diff / current_price < 0.001:  # Dentro de 0.1%
                return True
        
        return False
    
    def is_near_liquidity_zone(self, current_candle: pd.Series, liquidity_zones: List, bias: str) -> bool:
        """Verificar si el precio está cerca de una zona de liquidez relevante"""
        if not liquidity_zones:
            return False
        
        current_price = current_candle['close']
        relevant_zones = [
            zone for zone in liquidity_zones 
            if (bias == 'bullish' and zone['type'] == 'equal_low') or
               (bias == 'bearish' and zone['type'] == 'equal_high')
        ]
        
        for zone in relevant_zones[-5:]:  # Últimas 5 zonas relevantes
            price_diff = abs(current_price - zone['price'])
            if price_diff / current_price < 0.001:  # Dentro de 0.1%
                return True
        
        return False
    
    def detect_rejection_pattern(self, current_candle: pd.Series, 
                               previous_candle: pd.Series, bias: str) -> str:
        """Detectar patrones de vela de rechazo"""
        body = abs(current_candle['close'] - current_candle['open'])
        total_range = current_candle['high'] - current_candle['low']
        
        if total_range == 0:
            return None
        
        body_ratio = body / total_range
        
        # Doji - cuerpo pequeño
        if body_ratio < 0.1:
            return 'doji'
        
        # Martillo (alcista) o Estrella Fugaz (bajista)
        upper_wick = current_candle['high'] - max(current_candle['open'], current_candle['close'])
        lower_wick = min(current_candle['open'], current_candle['close']) - current_candle['low']
        
        if bias == 'bullish' and lower_wick > body * 2 and upper_wick < body:
            return 'hammer'
        elif bias == 'bearish' and upper_wick > body * 2 and lower_wick < body:
            return 'shooting_star'
        
        # Vela envolvente
        if (bias == 'bullish' and 
            current_candle['close'] > previous_candle['open'] and
            current_candle['open'] < previous_candle['close']):
            return 'bullish_engulfing'
        elif (bias == 'bearish' and 
              current_candle['close'] < previous_candle['open'] and
              current_candle['open'] > previous_candle['close']):
            return 'bearish_engulfing'
        
        return None
    
    def calculate_confidence(self, candle: pd.Series, pattern: str, bias: str) -> float:
        """Calcular confianza de la señal basada en múltiples factores"""
        confidence = 0.5  # Base
        
        # Ajustar por tipo de patrón
        pattern_weights = {
            'hammer': 0.8,
            'shooting_star': 0.8, 
            'bullish_engulfing': 0.7,
            'bearish_engulfing': 0.7,
            'doji': 0.5
        }
        
        confidence += pattern_weights.get(pattern, 0.5) - 0.5
        
        # Ajustar por volumen relativo (si está disponible)
        if 'tick_volume' in candle:
            volume_ratio = candle['tick_volume'] / 1000
            confidence += min(volume_ratio * 0.1, 0.2)  # Máximo 20% por volumen
        
        return max(0.1, min(0.9, confidence))  # Limitar entre 0.1 y 0.9