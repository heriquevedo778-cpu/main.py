import os
from flask import Flask, request, jsonify
from whatsapp_api_client_python import API
from openai import OpenAI

app = Flask(__name__)

ID_INSTANCIA = os.getenv("ID_INSTANCIA")
TOKEN_INSTANCIA = os.getenv("TOKEN_INSTANCIA")
OPENAI_KEY = os.getenv("OPENAI_KEY")

greenAPI = API.GreenApi(ID_INSTANCIA, TOKEN_INSTANCIA)
client = OpenAI(api_key=OPENAI_KEY)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        if data.get('typeWebhook') == 'incomingMessageReceived':
            msg_data = data.get('messageData', {})
            chat_id = data.get('senderData', {}).get('chatId')
            
            if msg_data.get('typeMessage') == 'imageMessage':
                url_imagen = msg_data['fileMessageData']['downloadUrl']
                
                # PROMPT RELAJADO: Para que no se ponga fresa la IA
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "Saca todos los números largos que veas. Casi siempre empiezan con 8952. No importa si terminan en F o no, tú pásame todo lo que parezca un código ICCID o de barras. Uno por línea y ya."
                                },
                                {
                                    "type": "image_url", 
                                    "image_url": {"url": url_imagen} # Quitamos el 'high' para que no se bloquee
                                }
                            ],
                        }
                    ]
                )
                
                resultado = response.choices[0].message.content
                greenAPI.sending.sendMessage(chat_id, f"🔍 *Lo que encontré:*\n\n{resultado}")

    except Exception as e:
        print(f"Error: {e}")
        
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
