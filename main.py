import os
import requests
from flask import Flask, request, jsonify
from whatsapp_api_client_python import API
from openai import OpenAI

app = Flask(__name__)

# Configuración segura mediante Variables de Entorno en Railway
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
        # 1. Verificar si es un mensaje de imagen entrante
        if data.get('typeWebhook') == 'incomingMessageReceived':
            msg_data = data.get('messageData', {})
            chat_id = data.get('senderData', {}).get('chatId')
            
            if msg_data.get('typeMessage') == 'imageMessage':
                # URL de la imagen enviada por WhatsApp
                url_imagen = msg_data['fileMessageData']['downloadUrl']
                
                # 2. Mandar la imagen a OpenAI para extraer los códigos
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extrae de esta imagen únicamente los códigos que comienzan con 8952 y terminan con la letra F. Entrégame solo la lista de códigos, uno por línea, sin texto adicional."},
                                {"type": "image_url", "image_url": {"url": url_imagen}}
                            ],
                        }
                    ],
                    max_tokens=1000
                )
                
                resultado = response.choices[0].message.content
                
                # 3. Enviar la lista de vuelta al usuario por WhatsApp
                greenAPI.sending.sendMessage(chat_id, f"✅ *Códigos SIM detectados:*\n\n{resultado}")

    except Exception as e:
        print(f"Error procesando el webhook: {e}")
        
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # Railway configura el puerto automáticamente a través de la variable PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
