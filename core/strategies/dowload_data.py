import pandas as pd
import datetime as dt

# Intentamos importar MetaTrader5
try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False

import yfinance as yf


def get_forex_data(symbol="EURUSD", timeframe="M1", days=365):
    """Descarga datos históricos reales, usando MT5 si está disponible o Yahoo Finance como respaldo."""

    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=days)

    # 1️⃣ Si está disponible MetaTrader5, intentamos usarlo
    if HAS_MT5:
        print(f"🔌 Intentando conexión con MetaTrader 5 para {symbol}...")
        if mt5.initialize():
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"⚠️ El símbolo {symbol} no existe en MT5 o no está visible.")
                mt5.shutdown()
            else:
                timeframe_dict = {
                    "M1": mt5.TIMEFRAME_M1,
                    "M5": mt5.TIMEFRAME_M5,
                    "M15": mt5.TIMEFRAME_M15,
                    "H1": mt5.TIMEFRAME_H1,
                    "D1": mt5.TIMEFRAME_D1,
                }

                rates = mt5.copy_rates_range(symbol, timeframe_dict.get(timeframe, mt5.TIMEFRAME_M1), start_date, end_date)
                mt5.shutdown()

                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df["time"] = pd.to_datetime(df["time"], unit="s")
                    df.set_index("time", inplace=True)
                    print(f"✅ Datos descargados de MetaTrader 5: {len(df)} filas")
                    return df
                else:
                    print("⚠️ No se recibieron datos desde MT5. Intentando Yahoo Finance...")

    # 2️⃣ Si no se pudo usar MT5, recurrimos a Yahoo Finance
    print(f"🌍 Descargando datos desde Yahoo Finance para {symbol}=X ...")

    try:
        df = yf.download(f"{symbol}=X", start=start_date, end=end_date, interval="1m")
        if df.empty:
            print("⚠️ Yahoo Finance no devolvió datos (puede que el intervalo 1m sea muy detallado).")
            df = yf.download(f"{symbol}=X", start=start_date, end=end_date, interval="1h")
        df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
        print(f"✅ Datos descargados de Yahoo Finance: {len(df)} filas")
        return df
    except Exception as e:
        print(f"❌ Error descargando desde Yahoo Finance: {e}")
        return None


if __name__ == "__main__":
    data = get_forex_data(symbol="EURUSD", timeframe="M1", days=365)
    if data is not None:
        data.to_csv("eurusd_data.csv")
        print("💾 Archivo guardado como eurusd_data.csv")
        print(data.head())
    else:
        print("🚫 No se pudieron obtener datos históricos.")
