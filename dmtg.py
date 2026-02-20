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
def home(): return "Bot IPTV con MongoDB y Captura de Datos Online"

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
ADMIN_ID = 1819487289  # Tu ID de Administrador
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# --- COMANDOS DE ADMINISTRADOR ---

@bot.message_handler(commands=['daralta'])
def alta_revendedor(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        nuevo_id = int(message.text.split()[1])
        col_revendedores.update_one({"user_id": nuevo_id}, {"$set": {"tipo": "revendedor"}}, upsert=True)
        bot.reply_to(message, f"✅ ID {nuevo_id} activado como Revendedor.")
    except:
        bot.reply_to(message, "❌ Uso: /daralta 12345678")

@bot.message_handler(commands=['darbaja'])
def baja_revendedor(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        baja_id = int(message.text.split()[1])
        col_revendedores.delete_one({"user_id": baja_id})
        bot.reply_to(message, f"🗑️ ID {baja_id} eliminado de revendedores.")
    except:
        bot.reply_to(message, "❌ Uso: /darbaja 12345678")

@bot.message_handler(commands=['lista'])
def ver_socios(message):
    if message.from_user.id != ADMIN_ID: return
    socios = col_revendedores.find()
    texto = "📋 **LISTA DE REVENDEDORES:**\n"
    for s in socios: texto += f"• ID: `{s['user_id']}`\n"
    bot.reply_to(message, texto if "•" in texto else "📭 No hay socios.", parse_mode="Markdown")

# --- LÓGICA DE MENÚS Y CAPTURA ---

def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar Demo", callback_data="op3")
    )
    return markup

def solicitar_contacto(cid):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    boton_contacto = types.KeyboardButton(text="📱 Compartir mi número para Demo", request_contact=True)
    markup.add(boton_contacto)
    bot.send_message(cid, "Para entregarte una demo, por favor comparte tu número de contacto usando el botón de abajo:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def recibir_contacto(message):
    cid = message.chat.id
    nombre = message.from_user.first_name
    telefono = message.contact.phone_number
    # Proceder a generar la demo con los datos capturados
    proceso_demo(cid, nombre, telefono)

def proceso_demo(cid, nombre, telefono=None):
    es_socio = col_revendedores.find_one({"user_id": cid}) is not None
    
    # Si no es socio, validar si ya pidió demo
    if not es_socio:
        usuario_existente = col_usuarios.find_one({"user_id": cid})
        if usuario_existente:
            bot.send_message(cid, f"👋 {nombre}, ya has solicitado una demo anteriormente. Contacta a un asesor.", reply_markup=menu_botones())
            return
        # Si es nuevo y no tenemos teléfono, pedirlo
        if telefono is None:
            solicitar_contacto(cid)
            return

    bot.send_message(cid, "⌛ Generando acceso, espera un momento...")
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    try:
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, 
                            json={"package": ID_PAQUETE, "rid": str(uuid.uuid4())[:8]}, verify=False)
        if res.status_code == 200:
            d = res.json()
            # Guardar en base de datos con teléfono
            if not es_socio:
                col_usuarios.insert_one({
                    "user_id": cid, 
                    "nombre": nombre, 
                    "telefono": telefono,
                    "registro": uuid.uuid4().hex
                })
            
            bot.send_message(cid, f"✅ DEMO GENERADA\n👤 User: {d.get('username')}\n🔑 Pass: {d.get('password')}\n🌐 URL: {URL_BASE}", reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(cid, "❌ Error: No hay créditos disponibles.")
    except:
        bot.send_message(cid, "❌ Error de conexión con el servidor.")

@bot.callback_query_handler(func=lambda call: True)
def respuesta_botones(call):
    cid = call.message.chat.id
    if call.data == "op1": bot.send_message(cid, "Contenido Premium: Deportes, Cine y Series en HD/4K.")
    elif call.data == "op2": bot.send_message(cid, "Instrucciones: Descarga la App '1Stream' o 'Purple IPTV'.")
    elif call.data == "op3": proceso_demo(cid, call.from_user.first_name)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def respuesta_texto(m):
    bot.send_message(m.chat.id, f"¡Hola {m.from_user.first_name}! Selecciona una opción del menú:", reply_markup=menu_botones())

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()