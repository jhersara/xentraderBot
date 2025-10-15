# pages/dashboard_view.py

import customtkinter as ctk
from PIL import Image
import os
from pathlib import Path

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, balance, profit_loss, open_positions):
        super().__init__(parent, fg_color="transparent")
        
        # Configurar grid layout principal
        self.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        self.grid_columnconfigure(3, weight=2, uniform="col")
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        # ---------- Live Tickets ----------
        tickets_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        tickets_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tickets_frame.grid_columnconfigure(0, weight=1)
        tickets_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        
        # Título
        title_label = ctk.CTkLabel(
            tickets_frame,
            text="🎫 Live Tickets",
            font=("Segoe UI", 16, "bold"),
            text_color="#89B4FA"
        )
        title_label.grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # Tickets principales
        ctk.CTkLabel(
            tickets_frame,
            text="23",
            font=("Segoe UI", 24, "bold"),
            text_color="#CDD6F4"
        ).grid(row=1, column=0, sticky="w", padx=15)
        
        ctk.CTkLabel(
            tickets_frame,
            text="Open",
            font=("Segoe UI", 12),
            text_color="#6C7086"
        ).grid(row=1, column=0, sticky="w", padx=(50, 0))
        
        # Tickets no asignados
        ctk.CTkLabel(
            tickets_frame,
            text="16",
            font=("Segoe UI", 18, "bold"),
            text_color="#F38BA8"
        ).grid(row=2, column=0, sticky="w", padx=15, pady=(5, 0))
        
        ctk.CTkLabel(
            tickets_frame,
            text="Unassigned",
            font=("Segoe UI", 11),
            text_color="#6C7086"
        ).grid(row=2, column=0, sticky="w", padx=(50, 0), pady=(5, 0))
        
        # Separador
        separator1 = ctk.CTkFrame(tickets_frame, height=1, fg_color="#313244")
        separator1.grid(row=3, column=0, sticky="ew", padx=15, pady=10)
        
        # Métricas de tiempo de respuesta
        metrics_frame = ctk.CTkFrame(tickets_frame, fg_color="transparent")
        metrics_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=5)
        metrics_frame.grid_columnconfigure((0, 1), weight=1)
        
        # FRT
        ctk.CTkLabel(
            metrics_frame,
            text="9 m",
            font=("Segoe UI", 16, "bold"),
            text_color="#A6E3A1"
        ).grid(row=0, column=0)
        
        ctk.CTkLabel(
            metrics_frame,
            text="FRT\nvs yesterday",
            font=("Segoe UI", 10),
            text_color="#6C7086",
            justify="center"
        ).grid(row=1, column=0)
        
        # SLA
        ctk.CTkLabel(
            metrics_frame,
            text="95%",
            font=("Segoe UI", 16, "bold"),
            text_color="#A6E3A1"
        ).grid(row=0, column=1)
        
        ctk.CTkLabel(
            metrics_frame,
            text="Within SLA",
            font=("Segoe UI", 10),
            text_color="#6C7086"
        ).grid(row=1, column=1)
        
        # ---------- CSAT ----------
        csat_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        csat_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        csat_frame.grid_columnconfigure(0, weight=1)
        csat_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkLabel(
            csat_frame,
            text="⭐ CSAT",
            font=("Segoe UI", 16, "bold"),
            text_color="#F9E2AF"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # CSAT actual
        ctk.CTkLabel(
            csat_frame,
            text="89%",
            font=("Segoe UI", 20, "bold"),
            text_color="#A6E3A1"
        ).grid(row=1, column=0, pady=5)
        
        ctk.CTkLabel(
            csat_frame,
            text="CSAT today",
            font=("Segoe UI", 11),
            text_color="#6C7086"
        ).grid(row=2, column=0)
        
        # CSAT comparativo
        ctk.CTkLabel(
            csat_frame,
            text="84%",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).grid(row=3, column=0, pady=(15, 5))
        
        # ---------- Métricas de Trading ----------
        trading_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        trading_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        trading_frame.grid_columnconfigure(0, weight=1)
        trading_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkLabel(
            trading_frame,
            text="📊 Trading Metrics",
            font=("Segoe UI", 16, "bold"),
            text_color="#CBA6F7"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # Drawdown
        drawdown_frame = ctk.CTkFrame(trading_frame, fg_color="transparent")
        drawdown_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        drawdown_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            drawdown_frame,
            text="-5.2%",
            font=("Segoe UI", 16, "bold"),
            text_color="#F38BA8"
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(
            drawdown_frame,
            text="Drawdown\nLast 30 Days +12%",
            font=("Segoe UI", 10),
            text_color="#6C7086",
            justify="right"
        ).grid(row=0, column=1, sticky="e")
        
        # Sharpe Ratio
        sharpe_frame = ctk.CTkFrame(trading_frame, fg_color="transparent")
        sharpe_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=5)
        sharpe_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            sharpe_frame,
            text="1.8",
            font=("Segoe UI", 16, "bold"),
            text_color="#A6E3A1"
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(
            sharpe_frame,
            text="Sharpe Ratio\nLast 30 Days +0.3",
            font=("Segoe UI", 10),
            text_color="#6C7086",
            justify="right"
        ).grid(row=0, column=1, sticky="e")
        
        # Volatility
        vol_frame = ctk.CTkFrame(trading_frame, fg_color="transparent")
        vol_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=5)
        vol_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            vol_frame,
            text="12.5%",
            font=("Segoe UI", 16, "bold"),
            text_color="#FAB387"
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(
            vol_frame,
            text="Volatility\nLast 30 Days +21%",
            font=("Segoe UI", 10),
            text_color="#6C7086",
            justify="right"
        ).grid(row=0, column=1, sticky="e")
        
        # ---------- Top Ticket Solvers ----------
        top_solvers_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        top_solvers_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        top_solvers_frame.grid_columnconfigure(0, weight=1)
        top_solvers_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        
        ctk.CTkLabel(
            top_solvers_frame,
            text="🏆 Top Performers",
            font=("Segoe UI", 16, "bold"),
            text_color="#89DCEB"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # Tabla de solvers
        solvers_data = [
            ("Reece Martin", "37"),
            ("Robyn Mers", "34"),
            ("Julia Smith", "27"),
            ("Ebenezer Grey", "24"),
            ("Marlon Brown", "23"),
            ("Heather Banks", "21")
        ]
        
        for i, (name, solved) in enumerate(solvers_data, 1):
            solver_frame = ctk.CTkFrame(top_solvers_frame, fg_color="transparent")
            solver_frame.grid(row=i, column=0, sticky="ew", padx=15, pady=2)
            solver_frame.grid_columnconfigure((0, 1), weight=1)
            
            ctk.CTkLabel(
                solver_frame,
                text=name,
                font=("Segoe UI", 11),
                text_color="#CDD6F4"
            ).grid(row=0, column=0, sticky="w")
            
            ctk.CTkLabel(
                solver_frame,
                text=solved,
                font=("Segoe UI", 11, "bold"),
                text_color="#89B4FA"
            ).grid(row=0, column=1, sticky="e")
        
        # ---------- New vs Closed Tickets ----------
        tickets_flow_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        tickets_flow_frame.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")
        tickets_flow_frame.grid_columnconfigure(0, weight=1)
        tickets_flow_frame.grid_rowconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            tickets_flow_frame,
            text="📈 Activity Flow",
            font=("Segoe UI", 16, "bold"),
            text_color="#94E2D5"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # Gráfico simulado
        chart_frame = ctk.CTkFrame(tickets_flow_frame, fg_color="#161622", corner_radius=10)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            chart_frame,
            text="New vs Closed Tickets Chart\n[Graph Visualization]",
            font=("Segoe UI", 12),
            text_color="#6C7086",
            justify="center"
        ).grid(row=0, column=0, sticky="nsew")
        
        # ---------- KPIs de Trading ----------
        kpi_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        kpi_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        kpi_frame.grid_columnconfigure((0, 1), weight=1)
        kpi_frame.grid_rowconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            kpi_frame,
            text="📊 Key Performance Indicators",
            font=("Segoe UI", 16, "bold"),
            text_color="#B4BEFE"
        ).grid(row=0, column=0, columnspan=2, pady=(15, 10), sticky="w", padx=15)
        
        # Total Trades & Win Rate
        trades_kpi = ctk.CTkFrame(kpi_frame, fg_color="transparent")
        trades_kpi.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        trades_kpi.grid_columnconfigure(0, weight=1)
        trades_kpi.grid_rowconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            trades_kpi,
            text="1,250",
            font=("Segoe UI", 20, "bold"),
            text_color="#89B4FA"
        ).grid(row=0, column=0)
        
        ctk.CTkLabel(
            trades_kpi,
            text="Total Trades\n+10%",
            font=("Segoe UI", 12),
            text_color="#6C7086",
            justify="center"
        ).grid(row=1, column=0)
        
        win_rate_kpi = ctk.CTkFrame(kpi_frame, fg_color="transparent")
        win_rate_kpi.grid(row=1, column=1, padx=15, pady=10, sticky="nsew")
        win_rate_kpi.grid_columnconfigure(0, weight=1)
        win_rate_kpi.grid_rowconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            win_rate_kpi,
            text="65%",
            font=("Segoe UI", 20, "bold"),
            text_color="#A6E3A1"
        ).grid(row=0, column=0)
        
        ctk.CTkLabel(
            win_rate_kpi,
            text="Win Rate\n+9%",
            font=("Segoe UI", 12),
            text_color="#6C7086",
            justify="center"
        ).grid(row=1, column=0)
        
        # Profit & Loss averages
        profit_kpi = ctk.CTkFrame(kpi_frame, fg_color="transparent")
        profit_kpi.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        profit_kpi.grid_columnconfigure(0, weight=1)
        profit_kpi.grid_rowconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            profit_kpi,
            text="$150",
            font=("Segoe UI", 18, "bold"),
            text_color="#A6E3A1"
        ).grid(row=0, column=0)
        
        ctk.CTkLabel(
            profit_kpi,
            text="Avg Profit\n+3%",
            font=("Segoe UI", 12),
            text_color="#6C7086",
            justify="center"
        ).grid(row=1, column=0)
        
        loss_kpi = ctk.CTkFrame(kpi_frame, fg_color="transparent")
        loss_kpi.grid(row=2, column=1, padx=15, pady=10, sticky="nsew")
        loss_kpi.grid_columnconfigure(0, weight=1)
        loss_kpi.grid_rowconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(
            loss_kpi,
            text="-$80",
            font=("Segoe UI", 18, "bold"),
            text_color="#F38BA8"
        ).grid(row=0, column=0)
        
        ctk.CTkLabel(
            loss_kpi,
            text="Avg Loss\n-3%",
            font=("Segoe UI", 12),
            text_color="#6C7086",
            justify="center"
        ).grid(row=1, column=0)
        
        # ---------- Recent Trades ----------
        trades_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        trades_frame.grid(row=2, column=2, rowspan=2, padx=10, pady=10, sticky="nsew")
        trades_frame.grid_columnconfigure(0, weight=1)
        trades_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        
        ctk.CTkLabel(
            trades_frame,
            text="🔄 Recent Trades",
            font=("Segoe UI", 16, "bold"),
            text_color="#F5C2E7"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        # Datos de trades recientes
        trades_data = [
            ("2024-07-15", "BTC/USD", "Buy", "0.5", "$30,000", "+$250"),
            ("2024-07-14", "ETH/USD", "Sell", "2", "$1,800", "-$100"),
            ("2024-07-14", "BTC/USD", "Buy", "0.3", "$29,500", "+$180"),
            ("2024-07-13", "LTC/USD", "Sell", "5", "$100", "-$50"),
            ("2024-07-13", "ETH/USD", "Buy", "1.5", "$1,750", "+$120")
        ]
        
        # Encabezados
        headers = ["Date", "Pair", "Type", "Size", "Price", "Result"]
        headers_frame = ctk.CTkFrame(trades_frame, fg_color="transparent")
        headers_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        headers_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                headers_frame,
                text=header,
                font=("Segoe UI", 10, "bold"),
                text_color="#89B4FA"
            ).grid(row=0, column=i, padx=2, sticky="w")
        
        # Filas de datos
        for row, (date, pair, type_, size, price, result) in enumerate(trades_data, 2):
            row_frame = ctk.CTkFrame(trades_frame, fg_color="transparent")
            row_frame.grid(row=row+1, column=0, sticky="ew", padx=15, pady=2)
            row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
            
            ctk.CTkLabel(row_frame, text=date, font=("Segoe UI", 9), text_color="#CDD6F4").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row_frame, text=pair, font=("Segoe UI", 9), text_color="#CDD6F4").grid(row=0, column=1, sticky="w")
            
            type_color = "#A6E3A1" if type_ == "Buy" else "#F38BA8"
            ctk.CTkLabel(row_frame, text=type_, font=("Segoe UI", 9), text_color=type_color).grid(row=0, column=2, sticky="w")
            
            ctk.CTkLabel(row_frame, text=size, font=("Segoe UI", 9), text_color="#CDD6F4").grid(row=0, column=3, sticky="w")
            ctk.CTkLabel(row_frame, text=price, font=("Segoe UI", 9), text_color="#CDD6F4").grid(row=0, column=4, sticky="w")
            
            result_color = "#A6E3A1" if result.startswith("+") else "#F38BA8"
            ctk.CTkLabel(row_frame, text=result, font=("Segoe UI", 9, "bold"), text_color=result_color).grid(row=0, column=5, sticky="w")
        
        # ---------- Customer Feedback ----------
        feedback_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        feedback_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        feedback_frame.grid_columnconfigure(0, weight=1)
        feedback_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        
        ctk.CTkLabel(
            feedback_frame,
            text="💬 Customer Feedback",
            font=("Segoe UI", 16, "bold"),
            text_color="#F9E2AF"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        feedbacks = [
            "Thanks for exchanging my item so promptly an hour ago",
            "Super fast resolution, thank you! an hour ago",
            "Great service as always 3 hours ago",
            "Helpful and efficient. Great service! 4 hours ago",
            "Fast and efficient, thanks. 2 days ago"
        ]
        
        for i, feedback in enumerate(feedbacks, 1):
            feedback_item = ctk.CTkFrame(feedback_frame, fg_color="#161622", corner_radius=8)
            feedback_item.grid(row=i, column=0, sticky="ew", padx=15, pady=3)
            feedback_item.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                feedback_item,
                text=feedback,
                font=("Segoe UI", 10),
                text_color="#CDD6F4",
                wraplength=200
            ).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        
        # ---------- Agent Status ----------
        agent_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        agent_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")
        agent_frame.grid_columnconfigure(0, weight=1)
        agent_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        
        ctk.CTkLabel(
            agent_frame,
            text="👥 Agent Status",
            font=("Segoe UI", 16, "bold"),
            text_color="#89DCEB"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=15)
        
        agents_data = [
            ("Ash Monk", "Offline"),
            ("Danica Johnson", "Away"),
            ("Ebenezer Grey", "Taking call"),
            ("Frank Massey", "Online"),
            ("Heather Banks", "Taking call"),
            ("Julia Smith", "Taking call"),
            ("Marlon Brown", "Taking call")
        ]
        
        for i, (name, status) in enumerate(agents_data, 1):
            agent_row = ctk.CTkFrame(agent_frame, fg_color="transparent")
            agent_row.grid(row=i, column=0, sticky="ew", padx=15, pady=2)
            agent_row.grid_columnconfigure((0, 1), weight=1)
            
            ctk.CTkLabel(
                agent_row,
                text=name,
                font=("Segoe UI", 10),
                text_color="#CDD6F4"
            ).grid(row=0, column=0, sticky="w")
            
            status_color = {
                "Online": "#A6E3A1",
                "Away": "#F9E2AF", 
                "Offline": "#6C7086",
                "Taking call": "#89B4FA"
            }.get(status, "#CDD6F4")
            
            ctk.CTkLabel(
                agent_row,
                text=status,
                font=("Segoe UI", 10),
                text_color=status_color
            ).grid(row=0, column=1, sticky="e")