import telebot
from telebot import types
import requests
import urllib3
import uuid
import os
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- SERVIDOR WEB PARA RENDER ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot IPTV con MongoDB Online"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- CONEXIÓN A MONGODB ATLAS ---
MONGO_URI = "mongodb+srv://guillermocs:Gu1ll3rm0.@cluster0.wx1wwso.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['iptv_business']
col_usuarios = db['usuarios_demos']

def ya_ha_pedido_demo(user_id):
    # Verifica si el ID de Telegram ya está registrado en la nube
    return col_usuarios.find_one({"user_id": user_id}) is not None

def registrar_solicitud(user_id, nombre):
    # Guarda el registro permanente
    col_usuarios.insert_one({
        "user_id": user_id, 
        "nombre": nombre,
        "fecha": uuid.uuid4().hex
    })

# --- CONFIGURACIÓN DEL BOT ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# --- TEXTOS ---
TXT_INFO = "Nuestro servicio incluye canales de paga, deportes, series y películas de todas las plataformas."
TXT_INST = "🤖 Android: https://play.google.com/store/search?q=1+stream\n🍎 iPhone: https://apps.apple.com/in/app/purple-iptv-lite-player/id6749171817"

def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar Demo", callback_data="op3")
    )
    return markup

def proceso_demo(cid, nombre):
    # 1. Validar en MongoDB antes de gastar créditos
    if ya_ha_pedido_demo(cid):
        bot.send_message(cid, f"👋 Hola {nombre}, ya has solicitado una demo anteriormente. Para contratar un plan, por favor contacta a un asesor.")
        return

    bot.send_message(cid, "⌛ Generando tus datos, espera un momento...")
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    
    try:
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, 
                            json={"package": ID_PAQUETE, "rid": str(uuid.uuid4())[:8]}, verify=False)
        if res.status_code == 200:
            d = res.json()
            # 2. Registrar en MongoDB con éxito
            registrar_solicitud(cid, nombre)
            msg = f"✅ DEMO GENERADA\n\n🌐 URL: https://tupdvr24.com\n👤 Usuario: {d.get('username')}\n🔑 Pass: {d.get('password')}"
            bot.send_message(cid, msg)
        else:
            bot.send_message(cid, "❌ No hay demos disponibles en este momento.")
    except:
        bot.send_message(cid, "❌ Error de conexión con el panel.")

@bot.message_handler(func=lambda m: True)
def respuesta_texto(m):
    cid = m.chat.id
    nombre = m.from_user.first_name
    if m.text == "1": bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif m.text == "2": bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif m.text == "3": proceso_demo(cid, nombre)
    else: bot.send_message(cid, f"¡Hola {nombre}! ¿Cómo puedo ayudarte hoy?", reply_markup=menu_botones())

@bot.callback_query_handler(func=lambda call: True)
def respuesta_botones(call):
    cid = call.message.chat.id
    nombre = call.from_user.first_name
    if call.data == "op1": bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif call.data == "op2": bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif call.data == "op3": proceso_demo(cid, nombre)
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()