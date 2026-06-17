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

HTML = """<!DOCTYPE html>
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
<div class="ad-banner rounded-xl p-3 text-center text-slate-900 font-bold text-sm">🔥 إشهار: أعلاف طبيعية 100% • توصيل مجاني في <span id="adCity">مدينتك</span> • اتصل: 0615957179</div>
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
<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586l-.707-.707A1 1 0 0013 4H7a1 1
