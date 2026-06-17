import os
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, session, abort
from flask_cors import CORS
# Optional: from flask_limiter import Limiter
# Optional: from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env when present (development)
load_dotenv()

# --- Configuration ---
APP_ENV = os.environ.get("FLASK_ENV", "production")
PORT = int(os.environ.get("PORT", 5000))
SECRET_KEY = os.environ.get("SECRET_KEY")  # set this in env for stable sessions in production
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not SECRET_KEY:
    # In development we can generate a key but in production require it be provided.
    if APP_ENV == "production":
        raise RuntimeError("SECRET_KEY environment variable is required in production")
    SECRET_KEY = os.urandom(24).hex()

# Validate API key early
if not GEMINI_API_KEY:
    # do not crash the app on import in dev, but log a clear error
    logging.warning("GEMINI_API_KEY is not set. Model calls will fail until it's provided.")

# --- App setup ---
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY
CORS(app, resources={r"/*": {"origins": "*"}})  # tighten this in production

# Optional rate limiter
# limiter = Limiter(app, key_func=get_remote_address, default_limits=["60 per minute"])

# Logging configuration
logging.basicConfig(level=logging.INFO if APP_ENV == "production" else logging.DEBUG)
logger = logging.getLogger("darija-ai")

# --- External API init (defensive) ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # choose model via env var for easier upgrades
    MODEL_NAME = os.environ.get("GENAI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(MODEL_NAME)
else:
    model = None
    MODEL_NAME = None

# --- Data (consider moving to JSON/DB) ---
VETS_DB: Dict[str, Dict[str, str]] = {
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


# --- Helpers ---
def get_vet_info(city: str) -> Dict[str, str]:
    return VETS_DB.get(city, {"name": "ما لقيتش", "phone": "----", "address": "تواصل معانا نزيدوه"})


def get_souk_today(now: Optional[datetime] = None) -> str:
    if now is None:
        now = datetime.now()
    return SOUKS.get(now.weekday(), "ما كاينش سوق اليوم")


def safe_trim_history(history: list, max_len: int = 20) -> list:
    """Trim history to a reasonable length to avoid huge payloads to the model."""
    if not isinstance(history, list):
        return []
    return history[-max_len:]


def build_system_prompt(city: str, souk_today: str, vet_info: Dict[str, str]) -> str:
    # Keep prompt concise and safe. Avoid inserting raw unvalidated user content.
    return (
        f"أنت Darija AI Pro، خبير فلاحي مغربي من {city}. "
        f"معلومات عن السوق اليوم: {souk_today}. "
        f"البيطري المحلي: {vet_info.get('name', 'غير متوفر')} - "
        f"هاتف: {vet_info.get('phone', '----')}. "
        "جاوب بالدارجة وبشكل عملي، واقترح حلول محلية، وكن موجزًا."
    )


def decode_base64_image(data_b64: str, limit_bytes: int = 5_000_000) -> Optional[bytes]:
    """Decode base64 image and enforce size limit. Return bytes or None."""
    try:
        header_sep = data_b64.find(",")
        if header_sep != -1:
            data_b64 = data_b64[header_sep + 1 :]
        img_bytes = base64.b64decode(data_b64)
        if len(img_bytes) > limit_bytes:
            logger.warning("Uploaded image too large: %d bytes", len(img_bytes))
            return None
        return img_bytes
    except Exception as e:
        logger.debug("Failed to decode image: %s", e)
        return None


# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME}), 200


@app.route("/set_city", methods=["POST"])
def set_city():
    payload = request.get_json(silent=True) or {}
    city = payload.get("city")
    if not city:
        return jsonify({"status": "error", "message": "city is required"}), 400
    session["city"] = city
    return jsonify({"status": "ok"}), 200


@app.route("/get_vet", methods=["POST"])
def get_vet():
    payload = request.get_json(silent=True) or {}
    city = payload.get("city") or session.get("city") or "المغرب"
    vet = get_vet_info(city)
    return jsonify(vet), 200


@app.route("/chat", methods=["POST"])
def chat():
    if model is None:
        return jsonify({"reply": "خدمة الموديل غير مُفعّلة. تأكد من GEMINI_API_KEY في المتغيرات."}), 503

    data: Dict[str, Any] = request.get_json(silent=True) or {}
    message: str = (data.get("message") or "").strip()
    if not message and not data.get("image"):
        return jsonify({"reply": "المرجو إرسال رسالة أو صورة."}), 400

    # Enforce content limits
    if len(message) > 4000:
        return jsonify({"reply": "الرسالة طويلة بزاف، خفّفها."}), 413

    history = safe_trim_history(data.get("history", []), max_len=20)
    city = data.get("city") or session.get("city") or "المغرب"
    souk_today = get_souk_today()
    vet_info = get_vet_info(city)

    system_prompt = build_system_prompt(city, souk_today, vet_info)

    # Prepare image if provided, decode and validate size
    image_b64 = data.get("image")
    image_bytes = None
    if image_b64:
        image_bytes = decode_base64_image(image_b64)
        if image_bytes is None:
            return jsonify({"reply": "فشل فـ معالجة الصورة أو الحجم كبير بزاف."}), 400

    try:
        # Start chat with limited history. The exact SDK surface may differ; adapt as needed.
        chat_session = model.start_chat(history=history)

        if image_bytes:
            # The SDK might accept images either as base64 string or bytes in a dict. Keep both options in mind.
            # Here we pass the base64 string to the SDK as before but only after validation.
            img_payload = {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode("ascii")}
            prompt = f"{system_prompt}\n\nالمستخدم قال: {message}\n\nحلل التصويرة و جاوب:"
            response = chat_session.send_message([prompt, img_payload])
        else:
            prompt = f"{system_prompt}\n\nالمستخدم: {message}\n\nجاوب:"
            response = chat_session.send_message(prompt)

        # Defensive: check attributes on response
        reply_text = getattr(response, "text", None)
        if reply_text is None:
            # Try other possible attribute names
            reply_text = getattr(response, "content", "") or str(response)

        # Log short summary
        logger.info("Chat reply size=%d for city=%s", len(reply_text), city)
        return jsonify({"reply": reply_text}), 200

    except Exception as e:
        logger.exception("Model error:")
        # Avoid leaking internals in production responses
        if APP_ENV == "production":
            return jsonify({"reply": "خطأ من الخدمة — محاولة لاحقاً."}), 502
        else:
            return jsonify({"reply": f"خطأ: تأكد من GEMINI_API_KEY فـ Railway Variables. {str(e)}"}), 502


if __name__ == "__main__":
    debug_flag = APP_ENV != "production"
    app.run(host="0.0.0.0", port=PORT, debug=debug_flag)
