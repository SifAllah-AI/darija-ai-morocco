from flask import Flask, render_template_string, request, jsonify, session
import google.generativeai as genai
import base64
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

HTML = '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Darija AI Pro | الخبير الفلاحي الذكي</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
body { font-family: 'Cairo', sans-serif; }
.gradient-bg { background: linear-gradient(135deg, #020617 0%, #0f172a 25%, #134e4a 100%); }
.glass { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(20, 184, 166, 0.3); }
.msg-user { background: linear-gradient(135deg, #0d9488, #14b8a6); }
.msg-ai { background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(20, 184, 166, 0.3); }
.glow-green { box-shadow: 0 0 30px rgba(20, 184, 166, 0.4); }
.ad-banner { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
</style>
</head>
<body class="gradient-bg min-h-screen text-white">
<div id="cityModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
<div class="glass rounded-3xl p-8 max-w-md w-full glow-green">
<h2 class="text-3xl font-bold mb-4 text-center bg-gradient-to-r from-teal-300 to-emerald-300 bg-clip-text text-transparent">مرحبا بيك a البطل 👋</h2>
<p class="text-slate-300 mb-6 text-center">باش نعاونك مزيان، قول ليا منين نتا؟</p>
<select id="citySelect" class="w-full bg-slate-800 border border-teal-500 rounded-xl px-4 py-3 mb-4 text-white">
<option value="">-- اختار المدينة ديالك --</option>
<option value="الدار البيضاء">الدار البيضاء</option>
<option value="الرباط">الرباط</option>
<option value="فاس">فاس</option>
<option value="مراكش">مراكش</option>
<option value="طنجة">طنجة</option>
<option value="أكادير">أكادير</option>
<option value="وجدة">وجدة</option>
<option value="مكناس">مكناس</option>
</select>
<button onclick="saveCity()" class="w-full bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 py-3 rounded-xl font-bold transition-all hover:scale-105">بدا المحادثة 🚀</button>
</div>
</div>
<div class="container mx-auto px-4 py-4 max-w-6xl h-screen flex flex-col">
<div class="mb-3">
<div class="glass rounded-2xl p-4 mb-3 flex items-center justify-between">
<div class="flex items-center gap-3">
<div class="w-12 h-12 bg-gradient-to-br from-teal-400 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/50">
<svg class="w-7 h-7" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
</div>
<div>
<h1 class="text-xl font-bold bg-gradient-to-r from-teal-300 to-emerald-300 bg-clip-text text-transparent">Darija AI Pro</h1>
<p class="text-xs text-teal-300/80" id="userCity">الخبير الفلاحي الذكي</p>
</div>
</div>
<button onclick="showVetInfo()" class="bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 px-4 py-2 rounded-lg text-sm font-semibold transition-all">🩺 بيطري قريب</button>
</div>
<div class="ad-banner rounded-xl p-3 text-center text-slate-900 font-bold text-sm">🔥 إشهار: أعلاف طبيعية 100% • توصيل مجاني في <span id="adCity">مدينتك</span> • اتصل: 0600000000</div>
</div>
<div id="chat" class="flex-1 glass rounded-2xl p-6 mb-4 overflow-y-auto space-y-4"></div>
<div class="glass rounded-2xl p-4">
<div id="preview" class="hidden mb-3 relative">
<img id="previewImg" class="w-20 h-20 object-cover rounded-lg">
<button onclick="clearImage()" class="absolute -top-2 -right-2 bg-red-500 rounded-full w-6 h-6 text-xs">×</button>
</div>
<div class="flex gap-3 items-end">
<button onclick="document.getElementById('fileInput').click()" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-xl transition-all">
<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/></svg>
</button>
<button onclick="document.getElementById('cameraInput').click()" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-xl transition-all">
<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586l-.707-.707A1 1 0 0013 4H7a1 1 0 00-.707.293L5.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/></svg>
</button>
<input type="file" id="cameraInput" accept="image/*" capture="environment" class="hidden" onchange="handleImage(this)">
<input type="file" id="fileInput" accept="image/*" class="hidden" onchange="handleImage(this)">
<textarea id="textInput" rows="1" placeholder="كتب رسالتك..." class="flex-1 bg-slate-800/50 border border-slate-600 rounded-xl px-4 py-3 focus:outline-none focus:border-teal-500 resize-none" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMessage()}"></textarea>
<button onclick="sendMessage()" class="bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 p-3 rounded-xl transition-all shadow-lg shadow-teal-500/30">
<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/></svg>
</button>
</div>
</div>
</div>
<script>
let currentImage = null;
let chatHistory = [];
let userCity = localStorage.getItem('userCity') || '';
window.onload = () => {
if (!userCity) {
document.getElementById('cityModal').classList.remove('hidden');
} else {
initChat();
}
}
function saveCity() {
const city = document.getElementById('citySelect').value;
if (!city) return alert('اختار المدينة a البطل');
userCity = city;
localStorage.setItem('userCity', city);
document.getElementById('cityModal').classList.add('hidden');
initChat();
fetch('/set_city', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({city: city})});
}
function initChat() {
document.getElementById('userCity').innerText = userCity;
document.getElementById('adCity').innerText = userCity;
addMessage(`السلام عليكم a ولد ${userCity} 👋\nأنا الخبير الفلاحي الذكي ديالك. مرحبا بيك.\n\nاليوم ${getTodaySouk()}\n\nشنو نقدر نعاونك اليوم؟ 🌱🐄`, false);
}
function getTodaySouk() {
const days = ['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'];
return days[new Date().getDay()];
}
function showVetInfo() {
fetch('/get_vet', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({city: userCity})}).then(r => r.json()).then(data => {
addMessage(`🩺 البيطري القريب ليك في ${userCity}:\n\n👨‍⚕️ الاسم: ${data.name}\n📞 الهاتف: ${data.phone}\n📍 العنوان: ${data.address}\n\nنعيط ليه دابا؟`, false);
});
}
function handleImage(input) {
const file = input.files[0];
if (!file) return;
currentImage = file;
document.getElementById('preview').classList.remove('hidden');
document.getElementById('previewImg').src = URL.createObjectURL(file);
input.value = '';
}
function clearImage() {
currentImage = null;
document.getElementById('preview').classList.add('hidden');
}
function addMessage(content, isUser, imageUrl = null) {
const chat = document.getElementById('chat');
const msg = document.createElement('div');
msg.className = isUser? 'flex justify-end' : '';
let html = `<div class="${isUser? 'msg-user' : 'msg-ai'} rounded-2xl ${isUser? 'rounded-tl-sm' : 'rounded-tr-sm'} p-4 max-w-[80%] ${isUser? 'ml-auto' : ''}">`;
if (!isUser) {
html += `<div class="flex items-center gap-2 mb-2"><div class="w-6 h-6 bg-teal-500 rounded-full flex items-center justify-center text-xs">AI</div><span class="text-teal-300 text-sm font-semibold">Darija AI</span></div>`;
}
if (imageUrl) html += `<img src="${imageUrl}" class="w-full rounded-lg mb-3 max-h-64 object-cover">`;
html += `<p class="text-slate-100 leading-relaxed whitespace-pre-wrap">${content}</p></div>`;
msg.innerHTML = html;
chat.appendChild(msg);
chat.scrollTop = chat.scrollHeight;
}
async function sendMessage() {
const textInput = document.getElementById('textInput');
const text = textInput.value.trim();
if (!text &&!currentImage) return;
let imageUrl = null;
let imageBase64 = null;
if (currentImage) {
imageUrl = URL.createObjectURL(currentImage);
const reader = new FileReader();
imageBase64 = await new Promise(resolve => {
reader.onload = e => resolve(e.target.result.split(',')[1]);
reader.readAsDataURL(currentImage);
});
}
addMessage(text || 'صيفطت ليك تصويرة', true, imageUrl);
textInput.value = '';
clearImage();
try {
const res = await fetch('/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: text, image: imageBase64, history: chatHistory, city: userCity})});
const data = await res.json();
addMessage(data.reply, false);
chatHistory.push({role: 'user', parts: [text || 'صورة']});
chatHistory.push({role: 'model', parts: [data.reply]});
} catch (err) {
addMessage('سمح ليا، وقع خطأ. عاود جرب', false);
}
}
document.getElementById('textInput').addEventListener('input', function() {
this.style.height = 'auto';
this.style.height = this.scrollHeight + 'px';
});
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

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
        chat = model.start_chat(history=history)
        system_prompt = f"أنت Darija AI Pro خبير فلاحي مغربي من {city}. المستخدم من {city}. اليوم: {souk_today}. البيطري المحلي: {vet_info.get('name', 'غير متوفر')} - {vet_info.get('phone', '')}. جاوب بالدارجة المغربية باختصار ووضوح. إلا كان المرض خطير اقترح البيطري المحلي."
        if image_b64:
            img = {'mime_type': 'image/jpeg', 'data': image_b64}
            prompt = f"{system_prompt}\n\nالمستخدم قال: {message}\n\nحلل التصويرة و جاوب:"
            response = chat.send_message([prompt, img])
        else:
            prompt = f"{system_prompt}\n\nالمستخدم: {message}\n\nجاوب:"
            response = chat.send_message(prompt)
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f'خطأ: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
