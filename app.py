from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import os
import base64

app = Flask(__name__)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

HTML_PAGE = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تبيب نّ الزرع و المواشي - Dr. Plant & Cattle</title>
    <style>
        body { font-family: Arial; background: #0a4d2e; color: white; text-align: center; padding: 10px; margin:0; }
       .box { background: #1a6b42; padding: 15px; border-radius: 15px; margin: 10px auto; max-width: 600px; }
        button, select { background: #ffd700; color: #0a4d2e; border: none; padding: 12px 20px; border-radius: 10px; font-size: 16px; font-weight: bold; margin: 5px; cursor: pointer; }
        input, textarea { width: 90%; padding: 10px; border-radius: 8px; border: none; margin: 5px 0; font-size: 16px; }
        input[type=file] { display: none; }
        #result { background: #0d5a36; padding: 15px; border-radius: 10px; margin-top: 15px; text-align: right; white-space: pre-wrap; }
        img { max-width: 100%; border-radius: 10px; margin: 10px 0; }
       .speak-btn { background: #4CAF50; color: white; }
       .share-btn { background: #25D366; color: white; }
       .tab { background: #0d5a36; padding: 10px; border-radius: 10px 10px 0 0; display: inline-block; margin: 0 2px; }
       .active { background: #ffd700; color: #0a4d2e; }
        h1 { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🌱🐄 تبيب نّ الزرع و المواشي</h1>
    <p>الخبير الأول فالمغرب لتشخيص أمراض النباتات و الحيوانات</p>

    <div class="box">
        <div>
            <span class="tab active" onclick="setMode('plant')">🌿 نباتات و أشجار</span>
            <span class="tab" onclick="setMode('animal')">🐄 مواشي و دواجن</span>
        </div>

        <select id="lang" onchange="updateLang()">
            <option value="darija">🇲🇦 دارجة مغربية</option>
            <option value="ar">🇸🇦 العربية الفصحى</option>
            <option value="fr">🇫🇷 Français</option>
            <option value="en">🇬🇧 English</option>
        </select>

        <input type="file" id="camera" accept="image/*" capture="environment">
        <input type="file" id="gallery" accept="image/*">
        <button onclick="document.getElementById('camera').click()">📸 صور بالكاميرا</button>
        <button onclick="document.getElementById('gallery').click()">🖼️ ختار تصويرة</button>

        <div id="preview"></div>
        <div id="result"></div>

        <button id="speakBtn" class="speak-btn" onclick="speak()" style="display:none;">🔊 سمع التشخيص</button>
        <button id="shareBtn" class="share-btn" onclick="share()" style="display:none;">📲 بارطاجي فـ WhatsApp</button>

        <div id="contact" style="margin-top:20px; display:none;">
            <h3>بغيتي يتواصلو معاك الخبراء؟</h3>
            <input type="text" id="name" placeholder="سميتك">
            <input type="tel" id="phone" placeholder="نمرة التيليفون WhatsApp">
            <button onclick="saveContact()">✅ تسجل و توصلك النصائح</button>
            <p id="contactMsg"></p>
        </div>
    </div>

    <script>
        let currentText = '';
        let currentMode = 'plant';
        let currentLang = 'darija';

        const langMap = {
            'darija': 'ar-SA', 'ar': 'ar-SA', 'fr': 'fr-FR', 'en': 'en-US'
        };

        document.getElementById('camera').onchange = upload;
        document.getElementById('gallery').onchange = upload;

        function setMode(mode) {
            currentMode = mode;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
        }

        function updateLang() {
            currentLang = document.getElementById('lang').value;
        }

        function upload(e) {
            const file = e.target.files[0];
            if (!file) return;

            document.getElementById('preview').innerHTML = '<img src="' + URL.createObjectURL(file) + '">';
            document.getElementById('result').innerHTML = 'كنحلل الصورة... صبر شوية 🤖';
            document.getElementById('speakBtn').style.display = 'none';
            document.getElementById('shareBtn').style.display = 'none';
            document.getElementById('contact').style.display = 'none';

            const reader = new FileReader();
            reader.onload = function() {
                fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        image: reader.result,
                        mode: currentMode,
                        lang: currentLang
                    })
                })
      .then(r => r.json())
      .then(data => {
                    currentText = data.result;
                    document.getElementById('result').innerHTML = '<b>التشخيص:</b><br>' + data.result;
                    document.getElementById('speakBtn').style.display = 'inline-block';
                    document.getElementById('shareBtn').style.display = 'inline-block';
                    document.getElementById('contact').style.display = 'block';
                    speak();
                })
      .catch(err => {
                    document.getElementById('result').innerHTML = 'وقع مشكل. عاود جرب';
                });
            };
            reader.readAsDataURL(file);
        }

        function speak() {
            if (!currentText) return;
            speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(currentText);
            utterance.lang = langMap[currentLang];
            utterance.rate = 0.9;
            const voices = speechSynthesis.getVoices();
            const voice = voices.find(v => v.lang.includes(langMap[currentLang].split('-')[0]));
            if (voice) utterance.voice = voice;
            speechSynthesis.speak(utterance);
        }

        function share() {
            const text = `🌱 تبيب نّ الزرع و المواشي 🔬\n\nالتشخيص:\n${currentText}\n\nجربو التطبيق فابور: ${window.location.href}`;
            window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
        }

        function saveContact() {
            const name = document.getElementById('name').value;
            const phone = document.getElementById('phone').value;
            if (!name ||!phone) {
                document.getElementById('contactMsg').innerHTML = 'عمر سميتك و النمرة عافاك';
                return;
            }
            // هنا تقدر تصيفطها لـ Google Sheet ولا Email من بعد
            document.getElementById('contactMsg').innerHTML = '✅ تسجلتي! غادي نتواصلو معاك فـ WhatsApp قريبا';
            fetch('/contact', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, phone: phone})
            });
        }

        speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        req = request.json
        data = req['image']
        mode = req['mode'] # plant or animal
        lang = req['lang'] # darija, ar, fr, en

        image_data = base64.b64decode(data.split(',')[1])

        prompts = {
            'plant': {
                'darija': "نتا خبير فلاحة مغربي سميتك تبيب نّ الزرع. شوف الصورة ديال النبتة/الشجرة و جاوب بالدارجة المغربية الشعبية. 1. شنو المرض؟ 2. علاش وقع؟ 3. الدوا: سميات أدوية كاينين فالمغرب + الثمن. 4. الوقاية. جاوب باختصار ومفهوم.",
                'ar': "أنت خبير زراعي. شخص مرض النبات/الشجرة في الصورة باللغة العربية الفصحى. 1. المرض 2. السبب 3. العلاج: أسماء أدوية متوفرة في المغرب مع السعر 4. الوقاية.",
                'fr': "Vous êtes un expert agronome. Diagnostiquez la maladie de la plante/arbre sur la photo en français. 1. Maladie 2. Cause 3. Traitement: noms de médicaments disponibles au Maroc + prix 4. Prévention.",
                'en': "You are an agricultural expert. Diagnose the plant/tree disease in the image in English. 1. Disease 2. Cause 3. Treatment: drug names available in Morocco + price 4. Prevention."
            },
            'animal': {
                'darija': "نتا بيطري مغربي خبير فالمواشي. شوف الصورة ديال البقرة/الغنمي/الدجاج و جاوب بالدارجة. 1. شنو المرض باين؟ 2. الأعراض 3. الدوا: سميات أدوية بيطرية فالمغرب + الثمن 4. نصائح. جاوب باختصار.",
                'ar': "أنت طبيب بيطري. شخص مرض الحيوان في الصورة بالعربية. 1. المرض 2. الأعراض 3. العلاج: أدوية بيطرية متوفرة في المغرب مع السعر 4. نصائح.",
                'fr': "Vous êtes vétérinaire. Diagnostiquez la maladie de l'animal sur la photo en français. 1. Maladie 2. Symptômes 3. Traitement: médicaments vétérinaires disponibles au Maroc + prix 4. Conseils.",
                'en': "You are a veterinarian. Diagnose the animal disease in the image in English. 1. Disease 2. Symptoms 3. Treatment: veterinary drugs available in Morocco + price 4. Advice."
            }
        }

        prompt = prompts[mode][lang]
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])
        return jsonify({"result": response.text})
    except Exception as e:
        return jsonify({"result": f"خطأ: {str(e)}"})

@app.route('/contact', methods=['POST'])
def contact():
    # هنا من بعد نقدرو نصيفطوها لـ Google Sheet ولا Email
    data = request.json
    print(f"New lead: {data['name']} - {data['phone']}") # كتبان فـ Railway Logs
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
