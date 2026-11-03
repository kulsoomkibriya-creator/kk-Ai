from flask import Flask, render_template, request, jsonify
from groq import Groq
import os, uuid, json

try:
    from google import genai
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

app = Flask(__name__)

# ======= KEYS YAHAN LAGAO JAAN =======

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""

groq_client = Groq(api_key=GROQ_API_KEY)

gemini_client = None
if GEMINI_AVAILABLE and len(GEMINI_API_KEY) > 20 and "YAHAN" not in GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1"})
        print("Gemini OK")
    except Exception as e:
        print("Gemini Fail:", e)
else:
    print("Gemini key nahi lagi")

MEMORY_FILE = "kulsoom_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return []
    return []

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data[-200:], f, ensure_ascii=False, indent=2)

SYSTEM_PROMPT = "You are KK Hijab Doll, Kulsoom's teacher like Meta AI. Teach ALL SUBJECTS: Commerce Accounting Journal Ledger, Math, Science, Computer, English, Urdu, Islamiat. Explain easy with trick. Same language as user. Cute friendly."

GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-safeguard-20b",
]

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
]

def get_reply(msg, history):
    msgs = [{"role":"system","content":SYSTEM_PROMPT}]
    for h in history[-6:]:
        msgs.append({"role":"user" if h['role']=='user' else "assistant", "content":h['text']})
    msgs.append({"role":"user","content":msg})

    for m in GROQ_MODELS:
        try:
            print(f"Trying Groq: {m}")
            r = groq_client.chat.completions.create(model=m, messages=msgs, max_tokens=1000, temperature=0.7)
            print(f"SUCCESS Groq: {m}")
            return r.choices[0].message.content
        except Exception as e:
            print(f"Fail Groq {m}: {e}")
            continue

    if gemini_client:
        for m in GEMINI_MODELS:
            try:
                print(f"Trying Gemini: {m}")
                resp = gemini_client.models.generate_content(model=m, contents=[SYSTEM_PROMPT + "\n\nUser: " + msg])
                print(f"SUCCESS Gemini: {m}")
                return resp.text
            except Exception as e:
                print(f"Fail Gemini {m}: {e}")
                continue

    return "Jaan dono fail ho gaye, key check karo"

@app.route('/')
def home(): return render_template('index.html', history=load_memory())

@app.route('/chat', methods=['POST'])
def chat():
    msg = request.form.get('message','') or (request.json.get('message','') if request.is_json else '')
    history = load_memory()
    ans = get_reply(msg, history)
    history.append({"id":str(uuid.uuid4()), "role":"user", "text":msg})
    history.append({"id":str(uuid.uuid4()), "role":"bot", "text":ans})
    save_memory(history)
    return jsonify({"reply":ans, "history":history})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)