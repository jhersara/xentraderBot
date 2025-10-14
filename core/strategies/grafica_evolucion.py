import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generar_datos_evolucion(num_trades=400, capital_inicial=100, win_rate=0.6, risk_reward=2):
    """
    Genera datos simulados de evolución de cuenta
    """
    capital = capital_inicial
    capitales = [capital]
    trades = [0]
    
    for i in range(1, num_trades + 1):
        # Simular resultado de trade (ganancia o pérdida)
        if random.random() < win_rate:  # Trade ganador
            resultado = capital * 0.01 * risk_reward  # 1% de riesgo, ratio 2:1
        else:  # Trade perdedor
            resultado = -capital * 0.01  # Pérdida del 1%
        
        capital += resultado
        capitales.append(capital)
        trades.append(i)
    
    return trades, capitales

def generar_grafica_evolucion(trades, capitales, output_file="evolucion_cuenta.png"):
    """
    Genera la gráfica de evolución de la cuenta
    """
    # Crear figura y eje
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Crear la gráfica principal
    ax.plot(trades, capitales, linewidth=2.5, color='#2E86AB', alpha=0.8)
    ax.fill_between(trades, capitales, alpha=0.2, color='#2E86AB')
    
    # Configurar límites del eje Y como en tu imagen
    ax.set_ylim(80000, 150000)
    
    # Configurar ticks del eje Y
    y_ticks = [80000, 90000, 100000, 110000, 120000, 130000, 140000, 150000]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(['80k', '90k', '100k', '110k', '120k', '130k', '140k', '150k'])
    
    # Configurar eje X
    ax.set_xlim(0, 400)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_xlabel('Número de Trades', fontsize=12, fontweight='bold')
    
    # Título y estilo
    ax.set_ylabel('Evolución de la Cuenta ($)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Remover bordes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_alpha(0.3)
    ax.spines['bottom'].set_alpha(0.3)
    
    # Añadir estadísticas
    capital_final = capitales[-1]
    profit_total = capital_final - capitales[0]
    profit_porcentaje = (profit_total / capitales[0]) * 100
    
    stats_text = f'Capital Final: ${capital_final:,.0f}\nProfit: {profit_porcentaje:+.1f}%'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def grafica_desde_datos_reales(operaciones, capital_inicial=10000, output_file="evolucion_real.png"):
    """
    Genera gráfica a partir de datos reales de operaciones
    """
    capital = capital_inicial
    capitales = [capital]
    trades = [0]
    
    for i, op in enumerate(operaciones, 1):
        capital += op['Resultado']
        capitales.append(capital)
        trades.append(i)
    
    return generar_grafica_evolucion(trades, capitales, output_file)

def grafica_desde_backtesting(archivo_resultados="resultados_backtest.csv", output_file="evolucion_backtest.png"):
    """
    Genera gráfica a partir de archivo de resultados del backtesting
    """
    try:
        # Cargar datos del backtesting
        df = pd.read_csv(archivo_resultados)
        
        capital_inicial = df['capital_inicial'].iloc[0] if 'capital_inicial' in df.columns else 10000
        capitales = [capital_inicial]
        trades = [0]
        
        # Reconstruir evolución
        capital_actual = capital_inicial
        for i, resultado in enumerate(df['Resultado'] if 'Resultado' in df.columns else []):
            capital_actual += resultado
            capitales.append(capital_actual)
            trades.append(i + 1)
        
        return generar_grafica_evolucion(trades, capitales, output_file)
        
    except FileNotFoundError:
        print("Archivo de resultados no encontrado. Generando datos de ejemplo...")
        trades, capitales = generar_datos_evolucion()
        return generar_grafica_evolucion(trades, capitales, output_file)

# Versión mejorada que se integra con tu backtesting
def generar_grafica_desde_operaciones(operaciones, capital_inicial=10000, output_file="evolucion_cuenta.png"):
    """
    Genera gráfica directamente desde las operaciones de tu estrategia ICT
    """
    capital = capital_inicial
    capitales = [capital]
    trades = [0]
    fechas = [datetime.now() - timedelta(days=400)]  # Fecha inicial aproximada
    
    for i, op in enumerate(operaciones, 1):
        capital += op['Resultado']
        capitales.append(capital)
        trades.append(i)
        # Usar fecha de entrada de la operación o generar una progresión
        if 'Fecha de entrada' in op:
            fechas.append(op['Fecha de entrada'])
        else:
            fechas.append(fechas[-1] + timedelta(days=1))
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Gráfica principal
    ax.plot(trades, capitales, linewidth=2.5, color='#2E86AB', alpha=0.8)
    ax.fill_between(trades, capitales, alpha=0.2, color='#2E86AB')
    
    # Configuración de ejes (igual que tu imagen)
    ax.set_ylim(80000, 150000)
    y_ticks = [80000, 90000, 100000, 110000, 120000, 130000, 140000, 150000]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(['80k', '90k', '100k', '110k', '120k', '130k', '140k', '150k'])
    
    ax.set_xlim(0, 400)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_xlabel('Número de Trades', fontsize=12, fontweight='bold')
    ax.set_ylabel('Evolución de la Cuenta ($)', fontsize=12, fontweight='bold')
    
    # Grid y estilo
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Estadísticas
    capital_final = capitales[-1]
    profit_total = capital_final - capital_inicial
    profit_porcentaje = (profit_total / capital_inicial) * 100
    
    stats_text = f'Capital Final: ${capital_final:,.0f}\nProfit: {profit_porcentaje:+.1f}%'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ Gráfica guardada como: {output_file}")
    print(f"📊 Estadísticas:")
    print(f"   - Capital inicial: ${capital_inicial:,.0f}")
    print(f"   - Capital final: ${capital_final:,.0f}")
    print(f"   - Profit: ${profit_total:,.0f} ({profit_porcentaje:+.1f}%)")
    print(f"   - Total trades: {len(operaciones)}")
    
    return fig

# Función principal para usar
def main():
    """
    Función principal - Ejecuta diferentes modos
    """
    print("📈 GENERADOR DE GRÁFICA DE EVOLUCIÓN")
    print("=" * 40)
    
    modo = input("Selecciona modo:\n1. Datos de ejemplo\n2. Desde operaciones ICT\n3. Desde archivo CSV\nOpción (1-3): ").strip()
    
    if modo == "1":
        # Generar datos de ejemplo
        trades, capitales = generar_datos_evolucion(num_trades=400, capital_inicial=100)
        generar_grafica_evolucion(trades, capitales, "evolucion_ejemplo.png")
        
    elif modo == "2":
        # Aquí integrarías con tus operaciones reales del backtesting
        print("Este modo requiere pasar las operaciones de tu estrategia ICT")
        # Ejemplo de uso:
        # operaciones = estrategia.operations  # Tus operaciones del backtesting
        # generar_grafica_desde_operaciones(operaciones, capital_inicial=10000)
        
    elif modo == "3":
        # Desde archivo CSV<<<
        archivo = input("Nombre del archivo CSV (default: resultados_backtest.csv): ").strip()
        if not archivo:
            archivo = "resultados_backtest.csv"
        grafica_desde_backtesting(archivo, "evolucion_backtest.png")
        
    else:
        print("Modo no reconocido. Generando ejemplo...")
        trades, capitales = generar_datos_evolucion()
        generar_grafica_evolucion(trades, capitales)

if __name__ == "__main__":
    main()