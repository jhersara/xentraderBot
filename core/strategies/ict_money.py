# Estrategia de ICT 
#import talib
from datetime import time
import math


class strategy_class:
    def __init__(self, data, symbol, decimal, swap, tamcontrato, velas_15M=3, velas_1M=30, ratio=2, risk=0.0):
        self.data = data.copy()

        #Parametros
        self.velas_m15 = velas_15M
        self.velas_m1 = velas_1M
        self.ratio = ratio
        self.risk = risk

        #Configuraciones
        self.cash = 100
        self.initial_cash = self.cash
        self.operations = []
        self.symbol = symbol
        self.fecha_actual = None
        self.decimal = decimal
        self.tamcontrato = tamcontrato
        self.position = 0

        #Esplipage
        #self.data['ATR'] = talib.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        self.data['splipage'] = self.data['ATR'] * 0.003


        #Calculamos las velas de m15
        data_m15 = data.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()