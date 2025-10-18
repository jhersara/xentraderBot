# mt5_adapter.py - MT5 Connection handler

import MetaTrader5 as mt5
import pandas as pd
from typing import Optional, Dict

class MT5Adapter:
    def _init_(self, mt5_config: Dict):
        self.config = mt5_config
        self.initialize_mt5()
    
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        if not mt5.initialize(
            path=self.config.get('path', ''),
            login=self.config.get('login', 0),
            password=self.config.get('password', ''),
            server=self.config.get('server', '')
        ):
            raise ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")
        return True
    
    def get_rates(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        """Get historical rates from MT5"""
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15
        }
        
        rates = mt5.copy_rates_from_pos(
            symbol, timeframe_map[timeframe], 0, count
        )
        return pd.DataFrame(rates) if rates is not None else pd.DataFrame()
    
    def place_order(self, order_request: Dict) -> Dict:
        """Place order through MT5"""
        result = mt5.order_send(order_request)
        return {
            'retcode': result.retcode,
            'order_id': result.order,
            'volume': result.volume,
            'price': result.price,
            'comment': result.comment
        }