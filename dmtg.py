import telebot
from telebot import types
import requests
import urllib3
import uuid
import os
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- SERVIDOR WEB PARA MANTENER VIVO ---
app = Flask(__name__)
@app.route('/')
def home(): return "Demos Producción - ESTABLE"

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
col_revendedores = db['revendedores']

# --- CONFIGURACIÓN DEL BOT ---
ADMIN_ID = 1819487289  
MI_CONTACTO_URL = "https://t.me/memcasas" 
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- TEXTOS ---
TXT_INFO = (
    "Nuestro servicio es TV por internet que incluye (todos los canales de paga de deportes, "
    "entretenimiento e infantiles), series y películas de todas las plataformas como Netflix, "
    "HBO, Disney + y más.\n\n"
    "Es como usar Netflix pero mas completo.\n\n"
    "Puedes usarlo en Teléfono, TV Smart y computadora y con diferentes aplicaciones."
)

TXT_INST = (
    "Para poder usar la demo tienes que descargar un programa:\n\n"
    "🤖 **Si usas Android (TV o Teléfono):**\n"
    "https://play.google.com/store/search?q=1+stream&c=apps&hl=es_MX\n\n"
    "🍎 **Si usas iPhone:**\n"
    "https://apps.apple.com/in/app/purple-iptv-lite-player/id6749171817"
)

# --- COMPONENTES ---
def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones / Descargas", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar Demo Gratis", callback_data="op3")
    )
    return markup

def boton_ventas():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 Hablar con un Asesor", url=MI_CONTACTO_URL))
    return markup

# --- LÓGICA DE DEMO ---
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
            bot.send_message(cid, f"👋 {nombre}, ya has solicitado una demo anteriormente. Si deseas contratar un plan mensual, contacta a nuestro equipo de ventas:", 
                             reply_markup=boton_ventas())
            return
        if telefono is None:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton(text="📱 Compartir mi número para Demo", request_contact=True))
            bot.send_message(cid, "Para entregarte tu acceso, por favor presiona el botón de abajo para compartir tu contacto:", reply_markup=markup)
            return

    bot.send_message(cid, "⌛ Generando acceso, espera un momento...")
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    try:
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, 
                            json={"package": ID_PAQUETE, "rid": str(uuid.uuid4())[:8]}, verify=False)
        if res.status_code == 200:
            d = res.json()
            if not es_socio:
                col_usuarios.insert_one({"user_id": cid, "nombre": nombre, "telefono": telefono, "registro": uuid.uuid4().hex})
            
            msg = f"✅ **DEMO GENERADA**\n\n👤 User: `{d.get('username')}`\n🔑 Pass: `{d.get('password')}`\n🌐 URL: `{URL_BASE}`"
            bot.send_message(cid, msg, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(cid, "❌ Error: Panel en mantenimiento.")
    except:
        bot.send_message(cid, "❌ Error de conexión.")

# --- COMANDOS ADMIN ---
@bot.message_handler(commands=['daralta'])
def alta_revendedor(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        nuevo_id = int(message.text.split()[1])
        col_revendedores.update_one({"user_id": nuevo_id}, {"$set": {"tipo": "revendedor"}}, upsert=True)
        bot.reply_to(message, f"✅ ID {nuevo_id} activado como Revendedor.")
    except: bot.reply_to(message, "Uso: /daralta [ID]")

@bot.message_handler(commands=['darbaja'])
def baja_revendedor(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        baja_id = int(message.text.split()[1])
        col_revendedores.delete_one({"user_id": baja_id})
        bot.reply_to(message, f"🗑️ ID {baja_id} eliminado de revendedores.")
    except: bot.reply_to(message, "Uso: /darbaja [ID]")

@bot.message_handler(commands=['lista'])
def ver_socios(message):
    if message.from_user.id != ADMIN_ID: return
    socios = col_revendedores.find()
    texto = "📋 **LISTA DE SOCIOS:**\n"
    for s in socios: texto += f"• `{s['user_id']}`\n"
    bot.reply_to(message, texto if "•" in texto else "Sin socios.", parse_mode="Markdown")

# --- INTERACCIÓN ---
@bot.callback_query_handler(func=lambda call: True)
def respuesta_botones(call):
    cid = call.message.chat.id
    if call.data == "op1": bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif call.data == "op2": bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif call.data == "op3": proceso_demo(cid, call.from_user.first_name)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def saludo(m):
    bot.send_message(m.chat.id, f"¡Hola {m.from_user.first_name}! Bienvenido a nuestro servicio de TV Premium.", reply_markup=menu_botones())

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()