import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- DATOS DE CONEXIÓN ---
BASE_URL_ADMIN = "https://tupdvr24.com:8443"
X_API_KEY = "pTdYxWG3CL0MK6uRJMD35VyDst2fX07tV7csSqtULslnTKpj9ofcpecoo6EXSAMbnfGGC9cLdF3GAO5ZAxwgdhJr96ZwxEHRRU38"
X_AUTH_USER = "pn8ILzbBifMetC7Oo58rD3zCOw0vnkMKyIGE120"

# EL ID QUE OBTUVISTE HACE UN MOMENTO
ID_A_PROBAR = "0522d1eb-34e2-4a1d-8cca-fc47f6906d80"

def intentar_mandar_mensaje_directo(uuid_linea):
    headers = {
        "X-Api-Key": X_API_KEY,
        "X-Auth-User": X_AUTH_USER,
        "Content-Type": "application/json"
    }

    # Intentaremos la ruta de actualización avanzada que es la que gestiona mensajes
    url = f"{BASE_URL_ADMIN}/ext/line/{uuid_linea}/update-advanced"
    
    # Probamos mandando el mensaje en los 3 campos posibles que usa 1-Stream
    payload = {
        "message": "PRUEBA DE MENSAJE DIRECTO - GUILLERMO",
        "reseller_notes": "PRUEBA DE MENSAJE DIRECTO - GUILLERMO",
        "notes": "PRUEBA DE MENSAJE DIRECTO - GUILLERMO",
        "rid": "force_msg_001"
    }

    print(f"[*] Intentando forzar mensaje al ID: {uuid_linea}...")

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        
        if response.status_code == 200:
            print("\n" + "!"*40)
            print("¡LO LOGRASTE! El servidor aceptó el mensaje.")
            print("Ahora abre la App con ese usuario y deberías verlo.")
            print("!"*40)
        elif response.status_code == 403:
            print(f"\n[-] ERROR 403: El servidor sigue prohibiendo la edición.")
            print("Explicación: Tienes permiso para crear, pero el dueño del")
            print("panel bloqueó la función 'update' para los revendedores.")
        else:
            print(f"[-] Error inesperado ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"[-] Fallo técnico en la conexión: {e}")

if __name__ == "__main__":
    intentar_mandar_mensaje_directo(ID_A_PROBAR)