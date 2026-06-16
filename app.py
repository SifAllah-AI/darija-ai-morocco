# Darija AI Morocco - تأسست 2026 فـ كنفودة
# المدير العام: سيف الله علي

print("السلام عليكم، أنا سيف الله")
print("هادي أول شركة ذكاء اصطناعي مغربي 100%")

# أول نظام ترجمة ديالنا
def darija_to_english(kalima):
    tarjama = {
        "السلام": "Hello",
        "لاباس": "I'm fine", 
        "شكرا": "Thank you",
        "كنفودة": "Kenfouda, Morocco",
        "الله يعاونك": "God help you"
    }
    return tarjama.get(kalima, "مزال خدام عليها")

# جرب المنتوج ديالنا
print("كلمة 'السلام' =", darija_to_english("السلام"))
print("كلمة 'كنفودة' =", darija_to_english("كنفودة"))
