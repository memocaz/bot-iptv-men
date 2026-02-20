import telebot
from telebot import types
import requests
import urllib3
import uuid

# Desactivar avisos de seguridad de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# --- TUS TEXTOS ORIGINALES ---
TXT_INFO = (
    "Nuestro servicio es TV por internet que incluye (todos los canales de paga de deportes entretenimiento e infantiles), "
    "series y películas de todas las plataformas como Netflix, HBO, Disney + y más.\n\n"
    "Es como usar Netflix pero mas completo.\n\n"
    "Puedes usarlo en Teléfono, TV Smart y computadora y con diferentes aplicaciones.\n\n"
    "Te puedo generar una demo de 3 horas para que compruebes el contenido."
)

TXT_INST = (
    "Para poder usar la demos tienes que descargar un programa\n\n"
    "🤖 Si usa Android (TV o teléfono):\n"
    "https://play.google.com/store/search?q=1+stream&c=apps&hl=es_MX\n\n"
    "🍎 Si usas iPhone:\n"
    "https://apps.apple.com/in/app/purple-iptv-lite-player/id6749171817"
)

# --- FUNCIÓN PARA EL MENÚ DE BOTONES ---
def menu_botones():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1️⃣ Información del servicio", callback_data="op1"),
        types.InlineKeyboardButton("2️⃣ Instrucciones para uso demo", callback_data="op2"),
        types.InlineKeyboardButton("3️⃣ Solicitar demo", callback_data="op3")
    )
    return markup

# --- LÓGICA DE GENERACIÓN DE DEMO ---
def proceso_demo(cid):
    bot.send_message(cid, "⌛ Generando tus datos para la configuración, por favor espera...")
    headers = {"X-Api-Key": API_KEY, "X-Auth-User": AUTH_USER, "Content-Type": "application/json"}
    try:
        # Usamos un ID de referencia único como ya lo habías hecho
        res = requests.post(f"{URL_BASE}/ext/line/create", headers=headers, json={"package": ID_PAQUETE, "rid": str(uuid.uuid4())[:8]}, verify=False)
        if res.status_code == 200:
            d = res.json()
            user = d.get('username')
            pwd = d.get('password')
            msg = f"✅ DEMO GENERADA\n\n🌐 URL: https://tupdvr24.com\n👤 Usuario: {user}\n🔑 Contraseña: {pwd}\n\nApp: 1-Stream Player"
            bot.send_message(cid, msg)
        else:
            bot.send_message(cid, "❌ Error: El servidor no permitió crear la línea.")
    except Exception as e:
        bot.send_message(cid, "❌ Error técnico al conectar con el servidor.")

# --- MANEJADOR DE TEXTO (Responde a números y saludos) ---
@bot.message_handler(func=lambda message: True)
def respuesta_texto(message):
    cid = message.chat.id
    nombre = message.from_user.first_name # Saludamos por nombre
    
    if message.text == "1":
        bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif message.text == "2":
        bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif message.text == "3":
        proceso_demo(cid)
    else:
        # Siempre damos la bienvenida completa si no es una opción numérica
        bienvenida = (
            f"¡Hola {nombre}! Gracias por ponerte en contacto con nosotros.\n"
            "¿En qué podemos ayudarte?"
        )
        bot.send_message(cid, bienvenida, reply_markup=menu_botones())

# --- MANEJADOR DE CLIC EN BOTONES ---
@bot.callback_query_handler(func=lambda call: True)
def respuesta_botones(call):
    cid = call.message.chat.id
    if call.data == "op1":
        bot.send_message(cid, TXT_INFO, reply_markup=menu_botones())
    elif call.data == "op2":
        bot.send_message(cid, TXT_INST, reply_markup=menu_botones())
    elif call.data == "op3":
        proceso_demo(cid)
    # Cerramos el relojito de Telegram
    bot.answer_callback_query(call.id)

print("Bot Híbrido Personalizado Activo...")
bot.polling()