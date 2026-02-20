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
def home(): return "Bot IPTV con MongoDB Online"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- CONEXIÓN A MONGODB ATLAS ---
# Asegúrate de que esta URL sea la correcta con tu usuario y contraseña
MONGO_URI = "mongodb+srv://guillermocs:Gu1ll3rm0.@cluster0.wx1wwso.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['iptv_business']
col_usuarios = db['usuarios_demos']
col_revendedores = db['revendedores']

# --- CONFIGURACIÓN DEL BOT ---
ADMIN_ID = 1819487289  # Tu ID confirmado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# --- COMANDOS DE ADMINISTRADOR (PRIORIDAD ALTA) ---

@bot.message_handler(commands=['daralta'])
def alta_revendedor(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 No tienes permisos.")
        return
    try:
        nuevo_id = int(message.text.split()[1])
        col_revendedores.update_one({"user_id": nuevo_id}, {"$set": {"tipo": "revendedor"}}, upsert=True)
        bot.reply_to(message, f"✅ ID {nuevo_id} activado como Revendedor.")
    except:
        bot.reply_to(message, "❌ Error. Uso: /daralta 12345678")

@bot.message_handler(commands=['darbaja'])
def baja_revendedor(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        baja_id = int(message.text.split()[1])
        col_revendedores.delete_one({"user_id": baja_id})
        bot.reply_to(message, f"🗑️ ID {baja_id} eliminado de revendedores.")
    except:
        bot.reply_to(message, "❌ Uso: /darbaja 12345678")

# --- LÓGICA DE BOTONES Y DEMO ---

def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar Demo", callback_data="op3")
    )
    return markup

def proceso_demo(cid, nombre):
    es_socio = col_revendedores.find_one({"user_id": cid}) is not None
    if not es_socio and col_usuarios.find_one({"user_id": cid}):
        bot.send_message(cid, f"👋 {nombre}, ya has solicitado una demo anteriormente. Contacta a un asesor.", reply_markup=menu_botones())
        return

    bot.send_message(cid, "⌛ Generando demo...")
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    try:
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, json={"package": ID_PAQUETE, "rid": str(uuid.uuid4())[:8]}, verify=False)
        if res.status_code == 200:
            if not es_socio: col_usuarios.insert_one({"user_id": cid, "nombre": nombre})
            d = res.json()
            bot.send_message(cid, f"✅ DEMO GENERADA\n👤 User: {d.get('username')}\n🔑 Pass: {d.get('password')}")
        else:
            bot.send_message(cid, "❌ Error en el panel.")
    except:
        bot.send_message(cid, "❌ Error de conexión.")

@bot.callback_query_handler(func=lambda call: True)
def respuesta_botones(call):
    cid = call.message.chat.id
    if call.data == "op1": bot.send_message(cid, "Info de canales y pelis.")
    elif call.data == "op2": bot.send_message(cid, "Instala 1Stream en Android.")
    elif call.data == "op3": proceso_demo(cid, call.from_user.first_name)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def respuesta_texto(m):
    bot.send_message(m.chat.id, f"¡Hola {m.from_user.first_name}! ¿Qué deseas hacer?", reply_markup=menu_botones())

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()