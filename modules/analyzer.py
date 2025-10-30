# modules/analyzer.py
import os, json, hashlib, re
import streamlit as st
from groq import Groq

# ============================================================
# ☁️ إعداد Groq (سحابي فقط)
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8", "ignore")).hexdigest()

@st.cache_data(show_spinner=False)
def _llm_json_only(prompt: str) -> str:
    """يستدعي Groq ويعيد استجابة نصية (يتوقع JSON فقط)."""
    if not client:
        raise RuntimeError("⚠️ GROQ_API_KEY غير مضبوط.")
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
    )
    return resp.choices[0].message.content.strip()

def _safe_json_loads(s: str):
    """يحاول استخراج JSON حتى لو أضاف النموذج نصوصاً زائدة."""
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"(\[.*\])", s, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except:
                pass
    return None

# ============================================================
# 💾 نظام كاش للترجمات (دائم ومحلي)
# ============================================================
CACHE_DIR = "cache_translations"
CACHE_FILE = os.path.join(CACHE_DIR, "translations.json")
os.makedirs(CACHE_DIR, exist_ok=True)

def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

@st.cache_data(show_spinner=False)
def translate_with_cache(text: str) -> str:
    """🌍 ترجمة ذكية إلى العربية مع كاش دائم"""
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    cache = _load_cache()

    if text_hash in cache:
        return cache[text_hash]

    st.info("🌍 يتم الآن ترجمة النص إلى العربية (مرة واحدة فقط)...")
    prompt = f"ترجم النص التالي إلى العربية ترجمة احترافية بدون حذف أو اختصار:\n{text[:20000]}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    translated = response.choices[0].message.content.strip()
    cache[text_hash] = translated
    _save_cache(cache)
    return translated

# ============================================================
# 📄 تحليل الأقسام مع أرقام الصفحات
# ============================================================
def analyze_sections_with_pages(doc_payload: dict):
    """
    doc_payload:
      - PDF: {"type":"pdf","pages":[{"page_num":1,"text":"..."}, ...]}
      - DOCX: {"type":"docx","text":"..."}
    يعيد قائمة أقسام JSON:
    [
      {"section":"...","summary":"...","start_page":1,"content":"..."}
    ]
    """
    st.info("☁️ جاري تحليل المستند عبر Groq…")

    if doc_payload.get("type") == "pdf":
        # دمج النصوص مع علامات الصفحة
        parts = [f"[[PAGE:{p['page_num']}]]\n{p['text']}" for p in doc_payload["pages"]]
        full = "\n\n".join(parts)
        clipped = full[:20000]

        prompt = f"""
اقرأ النص التالي (عرض فني) المرسل مع علامات صفحات بالشكل [[PAGE:n]].
قسّمه إلى أقسام رئيسية مثل: المقدمة، الأهداف، فهم المشروع، المنهجية، خطة التنفيذ، الفريق، النتائج، الخاتمة.
أعد النتيجة بصيغة JSON فقط بدون أي نص خارجه:

[
  {{
    "section": "اسم القسم",
    "summary": "ملخص القسم بالعربية",
    "start_page": رقم الصفحة التي يبدأ عندها القسم (استدل عليها من [[PAGE:n]]),
    "content": "النص الكامل للقسم كما هو دون حذف أو اختصار، واجمع الفقرات المتصلة من الصفحات المتتابعة"
  }}
]

النص المعلّم بالصفحات:
-----------------------
{clipped}
"""
        reply = _llm_json_only(prompt)
        data = _safe_json_loads(reply)

        if not data:
            st.warning("⚠️ لم يُرجع النموذج JSON صالحًا — تم حفظ النص كاملًا كقسم واحد.")
            return [{
                "section": "النص الكامل",
                "summary": "تحليل عام",
                "start_page": 1,
                "content": reply
            }]

        out = []
        for item in data:
            out.append({
                "section": str(item.get("section", "")).strip(),
                "summary": str(item.get("summary", "")).strip(),
                "start_page": int(item.get("start_page", 1) or 1),
                "content": str(item.get("content", "")).strip(),
            })
        return out

    elif doc_payload.get("type") == "docx":
        full = doc_payload["text"]
        clipped = full[:20000]
        prompt = f"""
اقرأ النص التالي (عرض فني). قسّمه إلى أقسام رئيسية مثل: المقدمة، الأهداف، المنهجية، خطة التنفيذ، الفريق، النتائج، الخاتمة.
أعد النتيجة بصيغة JSON فقط بهذا الشكل:
[
  {{
    "section": "اسم القسم",
    "summary": "ملخص القسم بالعربية",
    "start_page": 1,
    "content": "النص الكامل للقسم"
  }}
]
النص:
------
{clipped}
"""
        reply = _llm_json_only(prompt)
        data = _safe_json_loads(reply)
        if not data:
            return [{
                "section": "النص الكامل",
                "summary": "تحليل عام",
                "start_page": 1,
                "content": reply
            }]
        out = []
        for item in data:
            out.append({
                "section": str(item.get("section", "")).strip(),
                "summary": str(item.get("summary", "")).strip(),
                "start_page": 1,
                "content": str(item.get("content", "")).strip(),
            })
        return out

    else:
        st.error("صيغة الملف غير مدعومة.")
        return []

# ============================================================
# 🧠 الدالة الرئيسية لتحليل جميع العروض
# ============================================================
def analyze_all_offers(offers):
    """تحليل العروض واستخراج الأقسام + الترجمة + الكاش"""
    st.info("🤖 جاري تحليل العروض سحابيًا عبر Groq...")
    from modules.extractors import extract_text
    topics_data = {}

    for offer in offers:
        st.markdown(f"📂 **جاري تحليل العرض:** {offer.name}")
        try:
            full_text = extract_text(offer)
            if not full_text or len(full_text.strip()) < 200:
                st.warning(f"⚠️ النص في {offer.name} فارغ أو قصير جدًا")
                continue

            # إعداد الحمولة حسب نوع الملف
            if offer.name.lower().endswith(".pdf"):
                from modules.extractors import fitz
                doc = fitz.open(stream=offer.read(), filetype="pdf")
                offer.seek(0)
                pages = [{"page_num": i+1, "text": p.get_text("text")} for i, p in enumerate(doc)]
                payload = {"type": "pdf", "pages": pages}
            else:
                payload = {"type": "docx", "text": full_text}

            # تحليل الأقسام
            data = analyze_sections_with_pages(payload)
            topics_data[offer.name] = data
            st.success(f"✅ تم تحليل {offer.name} بنجاح.")

        except Exception as e:
            st.error(f"❌ خطأ أثناء تحليل {offer.name}: {e}")

    st.session_state.topics = topics_data
    st.success("🎯 تم تحليل جميع العروض واستخراج الأقسام.")

