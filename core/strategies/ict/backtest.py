import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse
import time
import warnings
from ict_lord import StrategyICTContinuous

warnings.filterwarnings('ignore')

class AdvancedICTBacktest:
    def __init__(self, symbol, capital_inicial=10000, risk=0.01):
        self.symbol = symbol
        self.capital_inicial = capital_inicial
        self.risk = risk
        self.tamcontrato = 100000
        self.decimal = 0.0001
        
    def ajustar_simbolo(self, symbol):
        """Ajusta el símbolo para MT5 (remueve la 'm' final)"""
        if symbol.upper().endswith('M'):
            return symbol.upper()[:-1]
        return symbol.upper()
    
    def inicializar_mt5(self):
        """Inicializa la conexión con MetaTrader 5"""
        if not mt5.initialize():
            print("Error al inicializar MT5")
            return False
        
        if not mt5.terminal_info():
            print("MT5 no está conectado al servidor")
            return False
            
        print("✅ Conexión con MT5 establecida")
        return True
    
    def verificar_simbolo(self):
        """Verifica y selecciona el símbolo en Market Watch"""
        print(f"🔍 Verificando símbolo: {self.symbol}")
        
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            print(f"❌ El símbolo {self.symbol} no se encuentra")
            return False
        
        if not symbol_info.visible:
            print(f"⚠️ El símbolo {self.symbol} no está en Market Watch. Agregando...")
            if not mt5.symbol_select(self.symbol, True):
                print(f"❌ No se pudo agregar {self.symbol} a Market Watch")
                return False
            print(f"✅ Símbolo {self.symbol} agregado a Market Watch")
        else:
            print(f"✅ Símbolo {self.symbol} disponible")
        
        return True
    
    def obtener_datos_rango(self, start_date, end_date):
        """Obtiene datos históricos de MT5"""
        print(f"📥 Solicitando datos desde {start_date} hasta {end_date}")
        
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, start_timestamp, end_timestamp)
        
        if rates is not None and len(rates) > 0:
            print(f"✅ Datos obtenidos: {len(rates)} velas M1")
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        
        print("❌ No se pudieron obtener datos")
        return None
    
    def obtener_datos_por_partes(self, start_date, end_date):
        """Obtiene datos por partes si el rango es muy grande"""
        print("🔄 Descargando datos por partes...")
        
        current_start = start_date
        all_data = []
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=30), end_date)
            
            print(f"📥 Descargando {current_start.date()} a {current_end.date()}...")
            
            start_timestamp = int(current_start.timestamp())
            end_timestamp = int(current_end.timestamp())
            
            rates = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M1, start_timestamp, end_timestamp)
            
            if rates is not None and len(rates) > 0:
                df_part = pd.DataFrame(rates)
                df_part['time'] = pd.to_datetime(df_part['time'], unit='s')
                df_part.set_index('time', inplace=True)
                all_data.append(df_part)
                print(f"   ✅ {len(rates)} velas descargadas")
            else:
                print(f"   ❌ No se pudieron obtener datos para este período")
            
            current_start = current_end + timedelta(days=1)
            time.sleep(0.1)
        
        if not all_data:
            return None
        
        final_df = pd.concat(all_data)
        final_df = final_df[~final_df.index.duplicated(keep='first')]
        final_df = final_df.sort_index()
        
        return final_df
    
    def generar_configuraciones(self):
        """Genera todas las configuraciones a probar en el orden específico"""
        ratios = [1, 2, 3, 4, 5]  # R1 a R5
        
        # CORREGIDO: Estructura R/M1/M15
        # M1 = velas_1M (temporalidad secundaria - minutos)
        # M15 = velas_15M (temporalidad primaria - 15 minutos)
        configuraciones_base = [
            (7, 7), (7, 11), (7, 15),    # R1/7M/7M, R1/7M/11M, R1/7M/15M
            (10, 9), (10, 13),           # R1/10M/9M, R1/10M/13M
            (13, 7), (13, 11), (13, 15), # R1/13M/7M, R1/13M/11M, R1/13M/15M
            (16, 9), (16, 13),           # R1/16M/9M, R1/16M/13M
            (19, 7), (19, 11), (19, 15), # R1/19M/7M, R1/19M/11M, R1/19M/15M
            (22, 9), (22, 13),           # R1/22M/9M, R1/22M/13M
            (25, 7), (25, 11), (25, 15), # R1/25M/7M, R1/25M/11M, R1/25M/15M
            (28, 9), (28, 13)            # R1/28M/9M, R1/28M/13M
        ]
        
        configuraciones = []
        for ratio in ratios:
            for m15_velas, m1_velas in configuraciones_base:
                configuraciones.append({
                    'ratio': ratio,
                    'velas_15M': m15_velas,  # Temporalidad PRIMARIA (15 minutos)
                    'velas_1M': m1_velas,    # Temporalidad SECUNDARIA (1 minuto)
                    'config_str': f'R{ratio}/{m1_velas}M/{m15_velas}M'  # Formato: R/M1/M15
                })
        
        return configuraciones
    
    def ejecutar_estrategia_ict_config(self, data, config):
        """Ejecuta la estrategia ICT con una configuración específica CORREGIDA"""
        try:
            # CORREGIDO: Parámetros mapeados correctamente
            estrategia = StrategyICTContinuous(
                data=data,
                symbol=self.symbol,
                decimal=self.decimal,
                swap=0,
                tamcontrato=self.tamcontrato,
                velas_15M=config['velas_15M'],  # Temporalidad PRIMARIA (15 minutos)
                velas_1M=config['velas_1M'],    # Temporalidad SECUNDARIA (1 minuto)
                ratio=config['ratio'],           # Ratio R
                risk=self.risk,
                initial_cash=self.capital_inicial
            )
            
            # Ejecutar la estrategia
            operaciones = estrategia.run()
            resultados = estrategia.get_results()
            
            # Calcular profit factor
            if operaciones:
                resultados_list = [op['Resultado'] for op in operaciones]
                ganancias = sum([r for r in resultados_list if r > 0])
                perdidas = abs(sum([r for r in resultados_list if r < 0]))
                
                profit_factor = ganancias / perdidas if perdidas > 0 else float('inf')
            else:
                profit_factor = 0
            
            return {
                'configuracion': config['config_str'],
                'ratio': config['ratio'],
                'm1_velas': config['velas_1M'],      # Temporalidad secundaria
                'm15_velas': config['velas_15M'],    # Temporalidad primaria
                'profit_factor': profit_factor,
                'win_rate': resultados['porcentaje_ganadas'],
                'profit_total': resultados['profit_total'],
                'total_operaciones': resultados['total_operaciones'],
                'operaciones_ganadas': resultados['operaciones_ganadas'],
                'capital_final': resultados['capital_final'],
                'operations': operaciones
            }
            
        except Exception as e:
            print(f"❌ Error en estrategia {config['config_str']}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def ejecutar_backtest_completo(self, meses=3):
        """Ejecuta backtesting completo para todas las configuraciones"""
        print("🔍 INICIANDO BACKTESTING AVANZADO ICT")
        print("=" * 60)
        print("📋 ESTRUCTURA: R{ratio}/{m1_velas}M/{m15_velas}M")
        print("   - R: Ratio TP/SL")
        print("   - M1: Velas de 1 minuto (secundaria)")
        print("   - M15: Velas de 15 minutos (primaria)")
        print("=" * 60)
        
        if not self.inicializar_mt5():
            return None
        
        try:
            if not self.verificar_simbolo():
                return None
            
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=meses * 30)
            
            print(f"📅 Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            print(f"💰 Capital inicial: ${self.capital_inicial:,.2f}")
            print(f"🎯 Símbolo: {self.symbol}")
            print(f"⏰ Duración: {meses} meses")
            print("=" * 60)
            
            # Obtener datos
            print("📥 Descargando datos históricos...")
            data = self.obtener_datos_rango(start_date, end_date)
            
            if data is None:
                print("⚠️ Intentando descarga por partes...")
                data = self.obtener_datos_por_partes(start_date, end_date)
            
            if data is None or len(data) == 0:
                print("❌ No se pudieron obtener datos históricos")
                return None
            
            print(f"✅ Datos obtenidos: {len(data)} velas M1")
            
            # Asegurar columnas necesarias
            if 'spread' not in data.columns:
                data['spread'] = 10
            
            # Generar configuraciones
            configuraciones = self.generar_configuraciones()
            print(f"🔄 Probando {len(configuraciones)} configuraciones...")
            print("📊 Estructura: R{ratio}/{m1_velas}M/{m15_velas}M")
            
            resultados = []
            
            for i, config in enumerate(configuraciones, 1):
                print(f"🔧 Ejecutando {i}/{len(configuraciones)}: {config['config_str']}")
                
                resultado = self.ejecutar_estrategia_ict_config(data, config)
                if resultado:
                    resultados.append(resultado)
                    print(f"   ✅ PF: {resultado['profit_factor']:.3f} | Ops: {resultado['total_operaciones']}")
                else:
                    print(f"   ❌ Error en configuración")
                
                time.sleep(0.1)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en backtesting completo: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            mt5.shutdown()
            print("🔌 Conexión con MT5 cerrada")
    
    def analizar_resultados(self, resultados):
        """Analiza y muestra los resultados organizados por Ratio"""
        if not resultados:
            print("❌ No hay resultados para analizar")
            return None
        
        print("\n" + "=" * 80)
        print("📊 RESULTADOS BACKTESTING AVANZADO ICT")
        print("📋 Estructura: R{ratio}/{m1_velas}M/{m15_velas}M")
        print("=" * 80)
        
        # Crear DataFrame
        df_resultados = pd.DataFrame([{
            'Configuracion': r['configuracion'],
            'Ratio': r['ratio'],
            'M1_Velas': r['m1_velas'],      # Temporalidad secundaria
            'M15_Velas': r['m15_velas'],    # Temporalidad primaria
            'Profit_Factor': r['profit_factor'],
            'Win_Rate': r['win_rate'],
            'Profit_Total': r['profit_total'],
            'Total_Operaciones': r['total_operaciones'],
            'Operaciones_Ganadas': r['operaciones_ganadas'],
            'Capital_Final': r['capital_final']
        } for r in resultados])
        
        # Mostrar resultados organizados por Ratio
        for ratio in [1, 2, 3, 4, 5]:
            print(f"\n🎯 RATIO R{ratio}:")
            print("-" * 50)
            
            configs_ratio = df_resultados[df_resultados['Ratio'] == ratio]
            # Ordenar por M15 (primaria) y luego por M1 (secundaria)
            configs_ratio = configs_ratio.sort_values(['M15_Velas', 'M1_Velas'])
            
            for _, config in configs_ratio.iterrows():
                pf_color = "🟢" if config['Profit_Factor'] > 1 else "🔴" if config['Profit_Factor'] > 0 else "⚫"
                print(f"   {pf_color} {config['Configuracion']}: PF={config['Profit_Factor']:.3f} | "
                      f"Win={config['Win_Rate']:.1f}% | Ops={config['Total_Operaciones']} | "
                      f"Profit=${config['Profit_Total']:,.0f}")
        
        # Estadísticas por Ratio
        print("\n📈 ESTADÍSTICAS POR RATIO:")
        print("-" * 40)
        
        for ratio in [1, 2, 3, 4, 5]:
            configs_ratio = df_resultados[df_resultados['Ratio'] == ratio]
            if not configs_ratio.empty:
                avg_pf = configs_ratio['Profit_Factor'].mean()
                max_pf = configs_ratio['Profit_Factor'].max()
                min_pf = configs_ratio['Profit_Factor'].min()
                configs_rentables = len(configs_ratio[configs_ratio['Profit_Factor'] > 1])
                
                print(f"R{ratio}: Avg PF: {avg_pf:.3f} | Max PF: {max_pf:.3f} | "
                      f"Min PF: {min_pf:.3f} | Rentables: {configs_rentables}/{len(configs_ratio)}")
        
        return df_resultados
    
    def generar_grafica_profit_factor_organizado(self, df_resultados):
        """Genera gráfica organizada por Ratio con colores diferentes"""
        try:
            # Colores para cada Ratio
            colores_ratio = {
                1: '#2E86AB',  # Azul
                2: '#A23B72',  # Magenta
                3: '#F18F01',  # Naranja
                4: '#C73E1D',  # Rojo
                5: '#2A9D8F'   # Verde
            }
            
            # Preparar datos organizados
            configuraciones_ordenadas = []
            profit_factors_ordenados = []
            colores = []
            
            # Ordenar por Ratio y luego por temporalidades
            for ratio in [1, 2, 3, 4, 5]:
                configs_ratio = df_resultados[df_resultados['Ratio'] == ratio]
                # Ordenar por M15 (primaria) y luego por M1 (secundaria)
                configs_ratio = configs_ratio.sort_values(['M15_Velas', 'M1_Velas'])
                
                for _, config in configs_ratio.iterrows():
                    configuraciones_ordenadas.append(config['Configuracion'])
                    profit_factors_ordenados.append(config['Profit_Factor'])
                    colores.append(colores_ratio[ratio])
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(20, 10))
            
            # Gráfica de barras organizada
            bars = ax.bar(configuraciones_ordenadas, profit_factors_ordenados, 
                         color=colores, alpha=0.7, edgecolor='black', linewidth=0.5)
            
            # Línea de profit factor = 1
            ax.axhline(y=1, color='red', linestyle='--', alpha=0.7, 
                      linewidth=2, label='Break-even (PF=1)')
            
            # Configurar ejes
            ax.set_ylabel('Profit Factor', fontsize=14, fontweight='bold')
            ax.set_xlabel('Configuración (Ratio/M1_Velas/M15_Velas)', 
                         fontsize=12, fontweight='bold')
            ax.set_title('Profit Factor por Configuración - Estrategia ICT\nEstructura: R{ratio}/{m1_velas}M/{m15_velas}M', 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Rotar etiquetas para mejor legibilidad
            plt.xticks(rotation=45, ha='right', fontsize=8)
            
            # Añadir grid
            ax.grid(True, alpha=0.3, axis='y')
            
            # Crear leyenda personalizada para los Ratios
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor=colores_ratio[1], label='R1'),
                Patch(facecolor=colores_ratio[2], label='R2'),
                Patch(facecolor=colores_ratio[3], label='R3'),
                Patch(facecolor=colores_ratio[4], label='R4'),
                Patch(facecolor=colores_ratio[5], label='R5')
            ]
            ax.legend(handles=legend_elements, loc='upper right', title="Ratios")
            
            # Ajustar layout
            plt.tight_layout()
            
            # Guardar gráfica
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"profit_factor_organizado_ict_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"✅ Gráfica organizada guardada como: {filename}")
            
            return fig
            
        except Exception as e:
            print(f"❌ Error generando gráfica organizada: {e}")
            return None

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Backtesting Avanzado ICT')
    parser.add_argument('--symbol', type=str, default='EURUSDm', help='Símbolo a operar')
    parser.add_argument('--capital', type=float, default=100, help='Capital inicial')
    parser.add_argument('--risk', type=float, default=0.01, help='Riesgo por operación')
    parser.add_argument('--meses', type=int, default=2, help='Meses de backtesting')
    
    args = parser.parse_args()
    
    # Crear y ejecutar backtesting
    backtest = AdvancedICTBacktest(
        symbol=args.symbol,
        capital_inicial=args.capital,
        risk=args.risk
    )
    
    # Ejecutar backtesting completo
    resultados = backtest.ejecutar_backtest_completo(meses=args.meses)
    
    if resultados:
        # Analizar resultados
        df_resultados = backtest.analizar_resultados(resultados)
        
        # Generar gráficas
        backtest.generar_grafica_profit_factor_organizado(df_resultados)
        
        print(f"\n🎉 Backtesting completado exitosamente!")
        print(f"📈 Se probaron {len(resultados)} configuraciones")
        
        # Mostrar mejores configuraciones
        mejores = df_resultados.nlargest(5, 'Profit_Factor')
        print(f"\n🏆 TOP 5 MEJORES CONFIGURACIONES:")
        for _, config in mejores.iterrows():
            print(f"   {config['Configuracion']}: PF={config['Profit_Factor']:.3f} | "
                  f"Win={config['Win_Rate']:.1f}% | Profit=${config['Profit_Total']:,.0f}")
        
    else:
        print("❌ No se pudieron obtener resultados del backtesting")

if __name__ == "__main__":
    main()