
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Настройки CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  

def generate_ai_reply(user_name, user_comment):
    """Генерация умного автоответа через OpenAI API (если есть ключ)"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and user_comment:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system", 
                        "content": "Ты — виртуальный AI-помощник. Напиши очень короткий, вежливый и дружелюбный автоответ на комментарий потенциального заказчика или работодателя."
                    },
                    {"role": "user", "content": f"Имя: {user_name}. Комментарий: {user_comment}"}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Ошибка OpenAI: {e}")
            
    # Резерв
    return (f"Здравствуйте, {user_name}! Спасибо за проявленный интерес. Ваше сообщение "
            f"успешно получено. Я ознакомлюсь с ним и свяжусь с вами в ближайшее время!")

def send_email(to_email, subject, body_text):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Внимание: Настройки SMTP не заданы.")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        print(f"Попытка подключения к {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        print("Письмо успешно отправлено!")
        return True
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА отправки Email: {str(e)}")
        return False

@app.route('/api/contact', methods=['POST'])
def contact_form():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Данные не получены"}), 400
            
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        message = (data.get('comment') or data.get('message') or '').strip()
        
        if not name or not email or not phone:
            return jsonify({"status": "error", "message": "Пожалуйста, заполните поля: Имя, Телефон и Email"}), 400
            
        ai_reply = generate_ai_reply(name, message)

        tg_text = (
            f"📬 *Новая заявка с портфолио!*\n\n"
            f"*Имя:* {name}\n"
            f"*Телефон:* {phone}\n"
            f"*Email:* {email}\n"
            f"*Сообщение:* {message if message else 'Без комментария'}\n\n"
            f"🤖 *AI Автоответ пользователя:* \n_{ai_reply}_"
        )
        
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": tg_text,
                "parse_mode": "Markdown"
            }
            try:
                requests.post(tg_url, json=payload, timeout=5)
            except Exception as e:
                print(f"Ошибка сети при отправке в TG: {e}")

        owner_subject = f"Новый лид: {name}"
        owner_body = (
            f"Получена новая заявка через форму обратной связи:\n\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Email: {email}\n"
            f"Сообщение: {message}\n\n"
            f"Отправленный AI-автоответ:\n{ai_reply}"
        )
        send_email(SENDER_EMAIL, owner_subject, owner_body)

        user_subject = "Ваше сообщение получено! (Алена / Python Developer)"
        user_body = (
            f"Здравствуйте, {name}!\n\n"
            f"Спасибо, что заполнили форму на моем сайте-портфолио.\n\n"
            f"🤖 Вот что думает мой AI-ассистент о вашем сообщении:\n"
            f"\"{ai_reply}\"\n\n"
            f"---\n"
            f"С уважением,\n"
            f"Алёна"
        )
        send_email(email, user_subject, user_body)

        return jsonify({
            "status": "success", 
            "message": "Сообщение успешно отправлено! Копия письма выслана на вашу почту."
        }), 200

    except Exception as e:
        print(f"Ошибка на сервере: {str(e)}")
        return jsonify({"status": "error", "message": "Произошла ошибка на сервере. Попробуйте позже."}), 500

if __name__ == '__main__':
    app.run(port=5000)
