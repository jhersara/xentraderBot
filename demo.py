import customtkinter as ctk
import webbrowser
from supabase import create_client

# Configura tu proyecto de Supabase
SUPABASE_URL = "https://rlnltxkgvpkfztkzotyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJsbmx0eGtndnBrZnp0a3pvdHlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4MTU0OTksImV4cCI6MjA3MzM5MTQ5OX0.SR-XYXW9TAOYYLxGAqDW8hExUaia4naQud-iNXnxMzU"   # nunca uses service_role en frontend
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------- INTERFAZ -------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("Login con Supabase (Google & Facebook)")
app.geometry("400x250")

def login_google():
    res = supabase.auth.sign_in_with_oauth({"provider": "google"})
    url = res.url
    webbrowser.open(url)  # abre navegador
    lbl_info.configure(text="Abre tu navegador y completa el login con Google.")

def login_facebook():
    res = supabase.auth.sign_in_with_oauth({"provider": "facebook"})
    url = res.url
    webbrowser.open(url)
    lbl_info.configure(text="Abre tu navegador y completa el login con Facebook.")

# ------------------- UI -------------------
lbl_title = ctk.CTkLabel(app, text="Bienvenido", font=("Arial", 20))
lbl_title.pack(pady=15)

btn_google = ctk.CTkButton(app, text="Login con Google", command=login_google)
btn_google.pack(pady=10)

btn_facebook = ctk.CTkButton(app, text="Login con Facebook", command=login_facebook)
btn_facebook.pack(pady=10)

lbl_info = ctk.CTkLabel(app, text="", font=("Arial", 12))
lbl_info.pack(pady=15)

app.mainloop()
