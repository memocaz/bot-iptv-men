import telebot
from telebot import types
import requests
import urllib3
import uuid
import os
import random
import string
from flask import Flask
from threading import Thread
from pymongo import MongoClient
from datetime import datetime

# --- SERVIDOR WEB PARA MANTENER VIVO (KEEP-ALIVE) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Demos Producción v1.1 - Sistema Estable"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- CONEXIÓN A MONGODB (CON AUTO-RECONEXIÓN) ---
MONGO_URI = "mongodb+srv://guillermocs:Gu1ll3rm0.@cluster0.wx1wwso.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['iptv_business']
col_usuarios = db['usuarios_demos']
col_revendedores = db['revendedores']

# --- CONFIGURACIÓN ---
ADMIN_ID = 1819487289  
MI_CONTACTO_URL = "https://t.me/guillermocs" 
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FUNCIÓN PARA GENERAR USUARIO PERSONALIZADO (3 LETRAS + 4 NÚMEROS) ---
def generar_usuario_pro(nombre):
    # Limpiar nombre (quitar espacios y caracteres raros)
    nombre_limpio = "".join(filter(str.isalnum, nombre)).upper()
    prefijo = nombre_limpio[:3] if len(nombre_limpio) >= 3 else (nombre_limpio + "XYZ")[:3]
    sufijo = "".join(random.choices(string.digits, k=4))
    return f"{prefijo}{sufijo}"

# --- MENÚS ---
def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones / Descargas", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar Demo Gratis", callback_data="op3")
    )
    return markup

# --- LÓGICA DE DEMOS ---
@bot.message_handler(content_types=['contact'])
def recibir_contacto(message):
    cid = message.chat.id
    nombre = message.from_user.first_name
    telefono = message.contact.phone_number
    proceso_demo(cid, nombre, telefono)

def proceso_demo(cid, nombre, telefono=None):
    es_socio = col_revendedores.find_one({"user_id": cid}) is not None
    
    if not es_socio:
        if col_usuarios.find_one({"user_id": cid}):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👨‍💻 Hablar con un Asesor", url=MI_CONTACTO_URL))
            bot.send_message(cid, f"👋 {nombre}, ya has usado tu demo. Para contratar el plan completo, contacta a nuestro asesor:", reply_markup=markup)
            return
        if telefono is None:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton(text="📱 Compartir mi número para Demo", request_contact=True))
            bot.send_message(cid, "Para entregarte tu demo, comparte tu contacto con el botón de abajo:", reply_markup=markup)
            return

    bot.send_message(cid, "⌛ Generando tu cuenta personalizada...")
    
    # GENERAR CREDENCIALES
    nuevo_user = generar_usuario_pro(nombre)
    nueva_pass = "".join(random.choices(string.digits, k=6))
    
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    payload = {
        "package": ID_PAQUETE,
        "username": nuevo_user,
        "password": nueva_pass
    }
    
    try:
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, json=payload, verify=False)
        if res.status_code == 200:
            if not es_socio:
                col_usuarios.insert_one({"user_id": cid, "nombre": nombre, "telefono": telefono, "fecha": datetime.now()})
                # AVISO PARA TI (ADMIN)
                bot.send_message(ADMIN_ID, f"🔔 **NUEVO LEAD:**\n👤 {nombre}\n📱 {telefono}\n🆔 `{nuevo_user}`")
            
            msg = f"✅ **DEMO LISTA**\n\n👤 User: `{nuevo_user}`\n🔑 Pass: `{nueva_pass}`\n🌐 URL: `{URL_BASE}`"
            bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(cid, "❌ Error en el panel (posiblemente usuario duplicado, reintenta).")
    except:
        bot.send_message(cid, "❌ Error de conexión.")

# --- COMANDOS ADMIN ---
@bot.message_handler(commands=['daralta', 'darbaja', 'lista', 'limpiar'])
def comandos_admin(message):
    if message.from_user.id != ADMIN_ID: return
    # (Aquí va la lógica de comandos que ya probamos en la v1.0)
    bot.reply_to(message, "Comando recibido (Admin Mode)")

# --- INICIO ---
@bot.message_handler(func=lambda m: True)
def saludo(m):
    bot.send_message(m.chat.id, f"¡Hola {m.from_user.first_name}! Bienvenido.", reply_markup=menu_botones())

if __name__ == "__main__":
    keep_alive()
    # Infinity polling con timeout largo para evitar caídas
    bot.infinity_polling(timeout=20, long_polling_timeout=10)