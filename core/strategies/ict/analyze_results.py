# analyze_results.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

class ResultAnalyzer:
    def __init__(self, operaciones, capital_evolution):
        self.operaciones = operaciones
        self.capital_evolution = capital_evolution
        self.df_operaciones = pd.DataFrame(operaciones)
    
    def analisis_detallado(self):
        """Análisis detallado de los resultados"""
        if self.df_operaciones.empty:
            print("No hay operaciones para analizar")
            return
        
        print("📈 ANÁLISIS DETALLADO DE OPERACIONES")
        print("=" * 50)
        
        # Por mes
        self.df_operaciones['Mes'] = self.df_operaciones['Fecha de entrada'].dt.to_period('M')
        resultado_mensual = self.df_operaciones.groupby('Mes')['Resultado'].sum()
        
        print("\n📅 RESULTADOS MENSUALES:")
        for mes, resultado in resultado_mensual.items():
            print(f"   {mes}: ${resultado:,.2f}")
        
        # Por tipo de operación
        resultado_tipo = self.df_operaciones.groupby('Tipo')['Resultado'].agg(['count', 'sum', 'mean'])
        print(f"\n🎯 POR TIPO DE OPERACIÓN:")
        print(resultado_tipo)
        
        # Drawdown analysis
        self.analizar_drawdown()
        
        # Generar reporte visual
        self.generar_reportes_visuales()
    
    def analizar_drawdown(self):
        """Analiza el drawdown de la estrategia"""
        capital_series = pd.Series(self.capital_evolution)
        rolling_max = capital_series.expanding().max()
        drawdown = (capital_series - rolling_max) / rolling_max * 100
        
        max_drawdown = drawdown.min()
        avg_drawdown = drawdown.mean()
        
        print(f"\n📉 ANÁLISIS DE DRAWDOWN:")
        print(f"   Drawdown máximo: {max_drawdown:.2f}%")
        print(f"   Drawdown promedio: {avg_drawdown:.2f}%")
        
        return max_drawdown, avg_drawdown
    
    def generar_reportes_visuales(self):
        """Genera reportes visuales completos"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Evolución del capital
        axes[0, 0].plot(self.capital_evolution)
        axes[0, 0].set_title('Evolución del Capital')
        axes[0, 0].set_ylabel('Capital ($)')
        axes[0, 0].grid(True)
        
        # 2. Drawdown
        capital_series = pd.Series(self.capital_evolution)
        rolling_max = capital_series.expanding().max()
        drawdown = (capital_series - rolling_max) / rolling_max * 100
        
        axes[0, 1].fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
        axes[0, 1].set_title('Drawdown (%)')
        axes[0, 1].set_ylabel('Drawdown %')
        axes[0, 1].grid(True)
        
        # 3. Distribución de resultados
        if not self.df_operaciones.empty:
            axes[1, 0].hist(self.df_operaciones['Resultado'], bins=20, alpha=0.7)
            axes[1, 0].axvline(0, color='red', linestyle='--')
            axes[1, 0].set_title('Distribución de Resultados')
            axes[1, 0].set_xlabel('Resultado ($)')
        
        # 4. Resultados mensuales
        if not self.df_operaciones.empty:
            monthly_results = self.df_operaciones.groupby(
                self.df_operaciones['Fecha de entrada'].dt.to_period('M')
            )['Resultado'].sum()
            axes[1, 1].bar(monthly_results.index.astype(str), monthly_results.values)
            axes[1, 1].set_title('Resultados Mensuales')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('analisis_detallado.png', dpi=300, bbox_inches='tight')
        plt.show()

# Uso del analizador
def analizar_resultados_backtest(operaciones, capital_evolution):
    analyzer = ResultAnalyzer(operaciones, capital_evolution)
    analyzer.analisis_detallado()