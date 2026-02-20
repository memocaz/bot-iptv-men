import telebot
from telebot import types
import requests
import urllib3
import uuid
import os
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB PARA RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot IPTV Vivo y Operando"

def run():
    # Render usa el puerto 10000 por defecto o el que asigne la variable PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- CONFIGURACIÓN ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# --- TEXTOS ---
TXT_INFO = (
    "Nuestro servicio es TV por internet con canales, series y películas.\n"
    "Puedes usarlo en Teléfono, TV Smart y computadora."
)

TXT_INST = (
    "🤖 Si usa Android:\n"
    "https://play.google.com/store/search?q=1+stream&c=apps&hl=es_MX"
)

# --- DEFINICIÓN DE MENÚ (Debe ir antes de usarse) ---
def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar Demo", callback_data="op3")
    )
    return markup

# --- LÓGICA DE DEMO ---
def proceso_demo(cid):
    bot.send_message(cid, "⌛ Generando tus datos, espera un momento...")
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    try:
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, json={"package": ID_PAQUETE, "rid": str(uuid.uuid4())[:8]}, verify=False)
        if res.status_code == 200:
            d = res.json()
            msg = f"✅ DEMO GENERADA\n👤 User: {d.get('username')}\n🔑 Pass: {d.get('password')}"
            bot.send_message(cid, msg)
        else:
            bot.send_message(cid, "❌ Error al generar demo.")
    except:
        bot.send_message(cid, "❌ Error de conexión.")

# --- MANEJADORES DE TELEGRAM ---
@bot.message_handler(func=lambda message: True)
def respuesta_texto(message):
    cid = message.chat.id
    nombre = message.from_user.first_name
    
    if message.text == "1":
        bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif message.text == "2":
        bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif message.text == "3":
        proceso_demo(cid)
    else:
        bot.send_message(cid, f"¡Hola {nombre}! Elige una opción:", reply_markup=menu_botones())

@bot.callback_query_handler(func=lambda call: True)
def respuesta_botones(call):
    cid = call.message.chat.id
    if call.data == "op1":
        bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif call.data == "op2":
        bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif call.data == "op3":
        proceso_demo(cid)
    bot.answer_callback_query(call.id)

# --- INICIO ---
if __name__ == "__main__":
    keep_alive()
    print("Bot en línea en Render...")
    bot.infinity_polling()