import os
import requests
from flask import Flask, request, jsonify
from whatsapp_api_client_python import API
from openai import OpenAI

app = Flask(__name__)

# Configuración mediante Variables de Entorno en Railway
ID_INSTANCIA = os.getenv("ID_INSTANCIA")
TOKEN_INSTANCIA = os.getenv("TOKEN_INSTANCIA")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Inicializar las APIs
greenAPI = API.GreenApi(ID_INSTANCIA, TOKEN_INSTANCIA)
client = OpenAI(api_key=OPENAI_KEY)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        # Detectar mensajes entrantes
        if data.get('typeWebhook') == 'incomingMessageReceived':
            msg_data = data.get('messageData', {})
            chat_id = data.get('senderData', {}).get('chatId')
            
            # Verificar si es una imagen
            if msg_data.get('typeMessage') == 'imageMessage':
                url_imagen = msg_data['fileMessageData']['downloadUrl']
                
                # Análisis de OpenAI con potencia máxima
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "Eres un experto en lectura de códigos ICCID. Analiza TODA la imagen de arriba hacia abajo. Extrae TODOS los códigos que empiecen con 8952 y terminen en F. No te saltes ninguno. Devuelve solo la lista de códigos, uno por línea."
                                },
                                {
                                    "type": "image_url", 
                                    "image_url": {
                                        "url": url_imagen,
                                        "detail": "high"  # Activa la máxima resolución para fotos borrosas
                                    }
                                }
                            ],
                        }
                    ],
                    max_tokens=1000
                )
                
                resultado = response.choices[0].message.content
                
                # Enviar respuesta al usuario
                if resultado and "8952" in resultado:
                    greenAPI.sending.sendMessage(chat_id, f"✅ *Códigos SIM detectados:*\n\n{resultado}")
                else:
                    greenAPI.sending.sendMessage(chat_id, "❌ No detecté códigos válidos. Intenta otra foto con mejor luz.")

    except Exception as e:
        print(f"Error procesando el webhook: {e}")
        
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # Railway asigna el puerto automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
