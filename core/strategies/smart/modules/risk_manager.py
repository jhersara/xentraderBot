# risk_manager.py - Risk management implementation
import numpy as np
from typing import Dict

class RiskManager:
    def _init_(self, risk_config: Dict):
        self.risk_percent = risk_config['risk_percent_per_trade']
        self.max_daily_trades = risk_config['max_daily_trades']
        self.max_consecutive_losses = risk_config['max_consecutive_losses']
        self.daily_trades = 0
        self.consecutive_losses = 0
        
    def calculate_position_size(self, balance: float, stop_pips: float, 
                              symbol: str) -> float:
        """Calculate lot size based on risk percentage"""
        risk_amount = balance * (self.risk_percent / 100)
        pip_value = self.get_pip_value(symbol)
        
        if pip_value > 0:
            lot_size = risk_amount / (stop_pips * pip_value)
            return round(lot_size, 2)
        return 0.0
    
    def get_pip_value(self, symbol: str) -> float:
        """Get pip value for symbol (simplified)"""
        if 'JPY' in symbol:
            return 0.01
        return 0.0001
    
    def can_trade(self) -> bool:
        """Check if trading is allowed"""
        return (self.daily_trades < self.max_daily_trades and 
                self.consecutive_losses < self.max_consecutive_losses)