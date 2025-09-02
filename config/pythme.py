import customtkinter as ctk

# Configuración inicial
ctk.set_appearance_mode("dark")  # "dark", "light", "system"
ctk.set_default_color_theme("pydracula.json")  # tu archivo de tema

root = ctk.CTk()
root.geometry("600x500")
root.title("Demo PyDracula Theme")

# ====== FRAME PRINCIPAL ======
frame = ctk.CTkFrame(root)
frame.pack(padx=20, pady=20, fill="both", expand=True)

# ====== LABEL ======
label = ctk.CTkLabel(frame, text="🐉 PyDracula Theme en acción", font=("Consolas", 22))
label.pack(pady=15)

# ====== BOTÓN ======
button = ctk.CTkButton(frame, text="Presióname")
button.pack(pady=10)

# ====== ENTRY ======
entry = ctk.CTkEntry(frame, placeholder_text="Escribe algo aquí...")
entry.pack(pady=10)

# ====== SWITCH ======
switch = ctk.CTkSwitch(frame, text="Activar opción")
switch.pack(pady=10)

# ====== SLIDER ======
slider = ctk.CTkSlider(frame, from_=0, to=100)
slider.pack(pady=10)

# ====== CHECKBOX ======
checkbox = ctk.CTkCheckBox(frame, text="Acepto los términos")
checkbox.pack(pady=10)

# ====== RADIOBUTTON ======
radio1 = ctk.CTkRadioButton(frame, text="Opción 1")
radio2 = ctk.CTkRadioButton(frame, text="Opción 2")
radio1.pack(pady=5)
radio2.pack(pady=5)

# ====== OPTION MENU ======
option_menu = ctk.CTkOptionMenu(frame, values=["Python", "JavaScript", "C++"])
option_menu.pack(pady=10)

# ====== COMBOBOX ======
combo = ctk.CTkComboBox(frame, values=["Opción A", "Opción B", "Opción C"])
combo.pack(pady=10)

# ====== TEXTBOX ======
textbox = ctk.CTkTextbox(frame, width=400, height=100)
textbox.insert("0.0", "Este es un textbox con el tema PyDracula 👾")
textbox.pack(pady=15)

root.mainloop()
