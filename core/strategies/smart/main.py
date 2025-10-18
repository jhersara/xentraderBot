# main.py core orchestration
# Codigo principal para programacion del bot Smart Money
import MetaTrader5 as mt5
import yaml
import logging
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar componentes (asegúrate de que estos archivos existan)
from core.strategies.smart.modules.mt5_adapter import MT5Adapter
from core.strategies.smart.modules.signal_engine import SignalEngine
from core.strategies.smart.modules.risk_manager import RiskManager
from core.strategies.smart.modules.execution_engine import ExecutionEngine
from telegram_bot import TelegramBot

class EstoicoTradingBot:
    def __init__(self, config_path="config.yaml"):
        self.load_config(config_path)
        self.setup_logging()
        self.setup_components()
        
    def load_config(self, config_path):
        """Cargar configuración desde YAML"""
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            
            # Reemplazar variables de entorno
            if 'mt5' in self.config:
                self.config['mt5']['password'] = os.getenv('MT5_PASSWORD', self.config['mt5'].get('password', ''))
            
            self.logger.info("Configuración cargada correctamente")
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            # Configuración por defecto
            self.config = {
                'mt5': {
                    'login': int(os.getenv('MT5_LOGIN', '0')),
                    'password': os.getenv('MT5_PASSWORD', ''),
                    'server': os.getenv('MT5_SERVER', ''),
                    'path': os.getenv('MT5_PATH', '')
                },
                'pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'timeframes': ['M15', 'M5', 'M1'],
                'risk': {
                    'max_daily_trades': 5,
                    'risk_per_trade': 0.02,
                    'max_drawdown': 0.1
                },
                'logging': {
                    'level': 'INFO',
                    'file': 'trading_bot.log'
                },
                'telegram': {
                    'enabled': False,
                    'token': os.getenv('TELEGRAM_TOKEN', ''),
                    'chat_id': os.getenv('TELEGRAM_CHAT_ID', '')
                }
            }
        
    def setup_logging(self):
        """Configurar sistema de logging"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file', 'trading_bot.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging configurado correctamente")
        
    def setup_components(self):
        """Inicializar todos los componentes del bot"""
        try:
            # Inicializar MT5 primero
            self.mt5 = MT5Adapter(self.config.get('mt5', {}))
            
            # Inicializar otros componentes
            self.signal_engine = SignalEngine(self.config.get('timeframes', ['M15', 'M5', 'M1']))
            self.risk_manager = RiskManager(self.config.get('risk', {}))
            self.execution_engine = ExecutionEngine(self.config.get('order', {}))
            
            # Telegram opcional
            telegram_config = self.config.get('telegram', {})
            if telegram_config.get('enabled', False) and telegram_config.get('token'):
                self.telegram = TelegramBot(telegram_config)
                self.logger.info("Telegram Bot inicializado")
            else:
                self.telegram = None
                self.logger.info("Telegram Bot deshabilitado")
            
            self.logger.info("Todos los componentes inicializados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando componentes: {e}")
            raise
    
    def run(self):
        """Bucle principal de trading"""
        self.logger.info("Iniciando bot de trading Estoico-Institucional")
        
        try:
            while True:
                self.logger.info("Ciclo de análisis iniciado")
                
                # Procesar cada símbolo
                pairs = self.config.get('pairs', ['EURUSD'])
                for symbol in pairs:
                    self.process_symbol(symbol)
                
                # Esperar entre ciclos (configurable)
                wait_time = self.config.get('cycle_wait', 60)  # 60 segundos por defecto
                self.logger.info(f"Esperando {wait_time} segundos para próximo ciclo...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            self.logger.info("Bot detenido por usuario")
        except Exception as e:
            self.logger.error(f"Error en bucle principal: {e}")
        finally:
            self.shutdown()
    
    def process_symbol(self, symbol):
        """Procesar un símbolo específico"""
        try:
            self.logger.debug(f"Procesando símbolo: {symbol}")
            
            # Obtener datos multi-timeframe
            m15_data = self.mt5.get_rates(symbol, "M15", 100)
            m5_data = self.mt5.get_rates(symbol, "M5", 50)
            m1_data = self.mt5.get_rates(symbol, "M1", 10)
            
            if m15_data is None or m5_data is None or m1_data is None:
                self.logger.warning(f"Datos insuficientes para {symbol}")
                return
            
            # Verificar si los datos están vacíos (depende de tu implementación de MT5Adapter)
            if hasattr(m15_data, 'empty') and m15_data.empty:
                self.logger.warning(f"Datos M15 vacíos para {symbol}")
                return
            
            # Generar señales
            signal = self.signal_engine.analyze(m15_data, m5_data, m1_data, symbol)
            
            if signal and self.risk_manager.can_trade():
                self.execute_trade(signal, symbol)
            elif signal:
                self.logger.info(f"Señal generada para {symbol} pero riesgo no permite trading")
            else:
                self.logger.debug(f"Sin señal para {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error procesando {symbol}: {e}")
    
    def execute_trade(self, signal, symbol):
        """Ejecutar trade basado en señal"""
        try:
            # Obtener balance actual
            account_info = mt5.account_info()
            if not account_info:
                self.logger.error("No se pudo obtener información de la cuenta")
                return
                
            balance = account_info.balance
            
            # Ejecutar trade
            result = self.execution_engine.execute_trade(
                signal, symbol, balance, self.risk_manager
            )
            
            if result and result.get('success'):
                self.logger.info(f"Trade ejecutado exitosamente: {symbol} - {result}")
                self.risk_manager.record_trade()
                
                # Notificar por Telegram
                if self.telegram:
                    self.telegram.send_trade_alert(symbol, signal, result)
            else:
                error_msg = result.get('error', 'Error desconocido') if result else 'Resultado vacío'
                self.logger.error(f"Error ejecutando trade en {symbol}: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"Error en execute_trade para {symbol}: {e}")
    
    def shutdown(self):
        """Apagar el bot correctamente"""
        self.logger.info("Apagando bot...")
        try:
            if hasattr(self, 'mt5'):
                self.mt5.shutdown()
            if hasattr(self, 'telegram'):
                self.telegram.shutdown()
            mt5.shutdown()
        except Exception as e:
            self.logger.error(f"Error durante el apagado: {e}")

if __name__ == "__main__":
    try:
        bot = EstoicoTradingBot("config.yaml")
        bot.run()
    except Exception as e:
        print(f"Error iniciando el bot: {e}")
        logging.error(f"Error iniciando el bot: {e}")