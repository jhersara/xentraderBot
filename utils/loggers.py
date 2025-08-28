# Manejador de eventos de login
# Importaciones 
import os
import logging
from logging.handlers import TimedRotatingFileHandler

# Crear la capeta de logs si no existe
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configuracion del loger
logger = logging.getLogger("xentrader_bot")
logger.setLevel(logging.DEBUG)

# Handler con rotacion diaria
log_file = os.path.join(LOG_DIR, "app.log")
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
handler.suffix = "%Y-%m-%d"

# Formato de los logs
formater = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formater)


# Evitar duplicados de Handlers 
if not logger.hasHandlers():
    logger.addHandler(handler)

# Funcion que estrae los handlers externios
def get_logger(name: str = "xentrader_bot"):
    return logger.getChild(name)