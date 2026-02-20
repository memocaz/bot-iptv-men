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
    # Render asigna obligatoriamente un puerto en esta variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # Evita que el servidor bloquee el cierre del bot
    t.start()

# --- CONFIGURACIÓN ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN_TELEGRAM = '7955911958:AAFPZ650mbXQRcmfKDBb3Jv6fB8p0c3d5PI'
API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"
URL_BASE = "https://tupdvr24.com:8443"
ID_PAQUETE = 91

bot = telebot.TeleBot(TOKEN_TELEGRAM)

# ... (Aquí mantienes tus funciones de menu_botones y textos iguales) ...

@bot.message_handler(func=lambda message: True)
def respuesta_texto(message):
    cid = message.chat.id
    nombre = message.from_user.first_name
    bot.send_message(cid, f"¡Hola {nombre}! Elige una opción:", reply_markup=menu_botones())

# --- INICIO SEGURO ---
if __name__ == "__main__":
    keep_alive() # Primero arranca el servidor que Render monitorea
    print("Servidor web iniciado para Render...")
    bot.infinity_polling() # Mayor estabilidad para el bot en la nube