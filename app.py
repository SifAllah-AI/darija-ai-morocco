from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

VETS_DB = {
    "الدار البيضاء": {"name": "د. أحمد البيطري", "phone": "0612345678", "address": "عين السبع"},
    "الرباط": {"name": "د. فاطمة الزهراء", "phone": "0623456789", "address": "أكدال"},
    "فاس": {"name": "د. يوسف البيطري", "phone": "0634567890", "address": "سايس"},
    "مراكش": {"name": "د. سعيد البيطري", "phone": "0645678901", "address": "جليز"},
    "طنجة": {"name": "د. كريم البيطري", "phone": "0656789012", "address": "بني مكادة"},
    "أكادير": {"name": "د. حسناء", "phone": "0667890123", "address": "تالبرجت"},
    "وجدة": {"name": "د. محمد البيطري", "phone": "0678901234", "address": "لازاري"},
    "مكناس": {"name": "د. رشيد", "phone": "0689012345", "address": "حمرية"},
}

SOUKS = {
    0: "الاثنين: سوق الاثنين في تازة، بركان، القنيطرة",
    1: "الثلاثاء: سوق ثلاثاء الأولاد في سطات، ثلاثاء سيدي بنور",
    2: "الأربعاء: سوق الأربعاء في الغرب، سوق الأربعاء ديال بني ملال",
    3: "الخميس: سوق الخميس في الفقيه بن صالح، خميس الزمامرة",
    4: "الجمعة: سوق الجمعة في مراكش، تارودانت، الصويرة",
    5: "السبت: سوق السبت في أولاد تايمة، سبت الكردان",
    6: "الأحد: سوق الأحد في أكادير، إنزكان، تيزنيت"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/set_city', methods=['POST'])
def set_city():
    session['city'] = request.json.get('city')
    return jsonify({'status': 'ok'})

@app.route('/get_vet', methods=['POST'])
def get_vet():
    city = request.json.get('city')
    vet = VETS_DB.get(city, {"name": "ما لقيتش", "phone": "----", "address": "تواصل معانا نزيدوه"})
    return jsonify(vet)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        image_b64 = data.get('image')
        history = data.get('history', [])
        city = data.get('city', 'المغرب')
        today = datetime.now().weekday()
        souk_today = SOUKS.get(today, "ما كاينش سوق اليوم")
        vet_info = VETS_DB.get(city, {})
        chat_session = model.start_chat(history=history)
        system_prompt = f"أنت Darija AI Pro خبير فلاحي مغربي من {city}. المستخدم من {city}. اليوم: {souk_today}. البيطري المحلي: {vet_info.get('name', 'غير متوفر')} - {vet_info.get('phone', '')}. جاوب بالدارجة المغربية باختصار ووضوح. إلا كان المرض خطير اقترح البيطري المحلي."
        if image_b64:
            img = {'mime_type': 'image/jpeg', 'data': image_b64}
            prompt = f"{system_prompt}\n\nالمستخدم قال: {message}\n\nحلل التصويرة و جاوب:"
            response = chat_session.send_message([prompt, img])
        else:
            prompt = f"{system_prompt}\n\nالمستخدم: {message}\n\nجاوب:"
            response = chat_session.send_message(prompt)
        return jsonify({'reply': response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'reply': f'خطأ: تأكد من GEMINI_API_KEY فـ Railway Variables. {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
