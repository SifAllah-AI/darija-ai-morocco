import os
import requests

# Darija AI Morocco - جيل 2026
# المدير العام: سيف الله علي

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
            {
                "role": "system",
                "content": "نتا ذكاء اصطناعي مغربي سميتك سيف، ولد الرباط. خدمتك تجاوب الناس بالدارجة المغربية ديال ولاد الرباط. ممنوع تهضر بالفصحى ولا بالإنجليزية. جاوب ديمة بدارجة مغربية زوينة و كون محترم و ضريف."
            },
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

print("السلام عليكم، أنا سيف")
print("أنا ذكاء اصطناعي مغربي ولد الرباط 🇲🇦")
print("هادي أول شركة ذكاء اصطناعي مغربي 100%")
print("--------------------------------")

while True:
    so2al = input("سولني a خويا: ")
    if so2al == "خروج":
        print("تهلا ف راسك a بطل")
        break
    jawab = ask_gemini(so2al)
    print("سيف:", jawab)
    print("--------------------------------")
