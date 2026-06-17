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
    <title>تبيب نّ الزرع - Tabib n'Zar3</title>
    <style>
        body { font-family: Arial; background: #0a4d2e; color: white; text-align: center; padding: 20px; }
   .box { background: #1a6b42; padding: 20px; border-radius: 15px; margin: 20px auto; max-width: 500px; }
        button { background: #ffd700; color: #0a4d2e; border: none; padding: 15px 30px; border-radius: 10px; font-size: 18px; font-weight: bold; margin: 10px; cursor: pointer; }
        input[type=file] { display: none; }
        #result { background: #0d5a36; padding: 15px; border-radius: 10px; margin-top: 20px; text-align: right; white-space: pre-wrap; }
        img { max-width: 100%; border-radius: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🌱 تبيب نّ الزرع</h1>
    <p>صور النبتة ديالك و نعطيك التشخيص و الدوا</p>
    <div class="box">
        <input type="file" id="camera" accept="image/*" capture="environment">
        <input type="file" id="gallery" accept="image/*">
        <button onclick="document.getElementById('camera').click()">📸 صور بالكاميرا</button>
        <button onclick="document.getElementById('gallery').click()">🖼️ ختار تصويرة</button>
        <div id="preview"></div>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('camera').onchange = upload;
        document.getElementById('gallery').onchange = upload;
        
        function upload(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            document.getElementById('preview').innerHTML = '<img src="' + URL.createObjectURL(file) + '">';
            document.getElementById('result').innerHTML = 'كنحلل الصورة... صبر شوية 🤖';
            
            const reader = new FileReader();
            reader.onload = function() {
                fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({image: reader.result})
                })
          .then(r => r.json())
          .then(data => {
                    document.getElementById('result').innerHTML = '<b>التشخيص:</b><br>' + data.result;
                })
          .catch(err => {
                    document.getElementById('result').innerHTML = 'وقع مشكل. عاود جرب';
                });
            };
            reader.readAsDataURL(file);
        }
    </script>
