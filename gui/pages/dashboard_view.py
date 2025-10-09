# pages/dashboard_view.py

import customtkinter as ctk

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, balance, profit_loss, open_positions):
        super().__init__(parent, fg_color="transparent")

        # Configurar grid layout
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # ---------- Resumen Financiero ----------
        financial_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        financial_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(
            financial_frame,
            text="💰 Resumen Financiero",
            font=("Segoe UI", 18, "bold"),
            text_color="#89B4FA"
        ).pack(pady=15)

        ctk.CTkLabel(
            financial_frame,
            text=f"Saldo Total: ${balance:,.2f}",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).pack(pady=8, padx=20, anchor="w")

        ctk.CTkLabel(
            financial_frame,
            text=f"Ganancias/Pérdidas: ${profit_loss:,.2f}",
            font=("Segoe UI", 14),
            text_color="#A6E3A1" if profit_loss >= 0 else "#F38BA8"
        ).pack(pady=8, padx=20, anchor="w")

        ctk.CTkLabel(
            financial_frame,
            text=f"Posiciones Abiertas: {open_positions}",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).pack(pady=8, padx=20, anchor="w")

        # ---------- Vista de Mercado ----------
        market_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        market_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(
            market_frame,
            text="📈 Vista de Mercado",
            font=("Segoe UI", 18, "bold"),
            text_color="#CBA6F7"
        ).pack(pady=15)

        ctk.CTkLabel(
            market_frame,
            text="Precio EURUSD: 1.0850",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).pack(pady=8, padx=20, anchor="w")

        ctk.CTkLabel(
            market_frame,
            text="Volumen: 125,000",
            font=("Segoe UI", 14),
            text_color="#CDD6F4"
        ).pack(pady=8, padx=20, anchor="w")

        ctk.CTkLabel(
            market_frame,
            text="[Gráfico de Velas Aquí]",
            font=("Segoe UI", 12),
            text_color="#6C7086"
        ).pack(pady=20, padx=20)

        # ---------- Operaciones Rápidas ----------
        operations_frame = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=15)
        operations_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(
            operations_frame,
            text="⚡ Operaciones Rápidas",
            font=("Segoe UI", 18, "bold"),
            text_color="#F9E2AF"
        ).pack(pady=15)

        buttons_frame = ctk.CTkFrame(operations_frame, fg_color="transparent")
        buttons_frame.pack(expand=True, fill="both", padx=20, pady=10)

        ctk.CTkButton(
            buttons_frame,
            text="🟢 Comprar",
            font=("Segoe UI", 14, "bold"),
            fg_color="#A6E3A1",
            hover_color="#94E2D5",
            text_color="#11111B",
            height=45,
            corner_radius=10
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            buttons_frame,
            text="🔴 Vender",
            font=("Segoe UI", 14, "bold"),
            fg_color="#F38BA8",
            hover_color="#F5C2E7",
            text_color="#11111B",
            height=45,
            corner_radius=10
        ).pack(side="left", expand=True, padx=5)

        ctk.CTkButton(
            buttons_frame,
            text="❌ Cerrar Posiciones",
            font=("Segoe UI", 14, "bold"),
            fg_color="#FAB387",
            hover_color="#F9E2AF",
            text_color="#11111B",
            height=45,
            corner_radius=10
        ).pack(side="left", expand=True, padx=5)
