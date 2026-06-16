from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

def ask_gemini(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-1.5-flash",
        "messages": [
            {"role": "system", "content": "جاوب بالدارجة المغربية و كون ضريف"},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

@app.route('/')
def home():
    return "أنا سيف الله AI 🇲🇦 - ذكاء اصطناعي مغربي خدام لايف"

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'GET':
        question = request.args.get('q', 'سلام')
    else:
        question = request.json.get('question', 'سلام')
    
    answer = ask_gemini(question)
    return jsonify({"question": question, "answer": answer})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
