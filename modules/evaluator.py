# modules/evaluator.py
import streamlit as st
import pandas as pd
import json, re, os
from groq import Groq
from dotenv import load_dotenv
from langdetect import detect
from deep_translator import GoogleTranslator
from modules.extractors import extract_text_with_pages  # التحديث هنا

# تحميل مفتاح Groq من .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ===========================================================
# 🔤 دالة اكتشاف اللغة وترجمة المعايير عند الحاجة
# ===========================================================
def translate_if_needed(criteria_list, text):
    """إذا كان العرض باللغة الإنجليزية، تُترجم المعايير تلقائيًا للإنجليزية"""
    try:
        sample = text[:1000]
        lang = detect(sample)
        if lang == "en":
            st.info("🔤 تم اكتشاف أن العرض باللغة الإنجليزية، يتم الآن ترجمة المعايير تلقائيًا...")
            translated = [
                GoogleTranslator(source="ar", target="en").translate(c)
                for c in criteria_list
            ]
            return translated, "en"
        else:
            return criteria_list, "ar"
    except Exception as e:
        st.warning(f"⚠️ لم يتم تحديد اللغة بدقة ({e})، سيتم استخدام المعايير كما هي.")
        return criteria_list, "ar"


# ===========================================================
# 🧠 الدالة الأساسية لتقييم العروض بالذكاء الاصطناعي
# ===========================================================
@st.cache_data(show_spinner=False)
def evaluate_offers(offers, criteria_list):
    results, details = [], {}

    for f in offers:
        with st.spinner(f"🔍 يتم تحليل العرض: {f.name}"):

            # ✅ تحديث: التعامل مع extract_text_with_pages
            data = extract_text_with_pages(f)
            if isinstance(data, dict):
                if data.get("type") == "pdf":
                    text = "\n".join(p["text"] for p in data.get("pages", []))
                elif data.get("type") == "docx":
                    text = data.get("text", "")
                else:
                    text = ""
            else:
                text = str(data)

            if not text.strip():
                st.warning(f"⚠️ لم يتم استخراج نص من الملف: {f.name}")
                continue

            # ترجمة المعايير إن لزم
            criteria_list, lang_detected = translate_if_needed(criteria_list, text)
            text_criteria = "\n".join([f"- {c}" for c in criteria_list])

            # ===== بناء التوجيه للنموذج (Prompt) =====
            prompt = f"""
أنت خبير تقييم عروض فنية وتقنية.
اقرأ النص التالي المأخوذ من عرض فني، ثم قيّم العرض بناءً على المعايير التالية:

لكل معيار:
- ضع درجة من 1 إلى 4 (1 = ضعيف، 4 = ممتاز)
- اكتب السؤال الذي طرحته على نفسك لتقييمه (ai_question)
- اشرح السبب المنطقي للدرجة (reason)

بعد الانتهاء من المعايير، أضف في النهاية مفتاحًا جديدًا باسم:
"overall_comment": يحتوي على ملاحظات عامة وشاملة عن العرض.

أعد النتيجة بصيغة JSON فقط كالتالي:
{{
  "scores": [
    {{
      "criterion": "اسم المعيار",
      "score": رقم من 1 إلى 4,
      "ai_question": "السؤال الذي طرحه المقيم",
      "reason": "السبب المنطقي للتقييم"
    }}
  ],
  "overall_comment": "ملاحظات عامة عن العرض ككل"
}}

المعايير:
{text_criteria}

النص الكامل للعرض الفني (بدون اختصار):
{text[:20000]}

رجاءً أعد النتيجة بالعربية فقط.
"""

            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    temperature=0.3,
                    max_tokens=3500,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.choices[0].message.content.strip()
                print("🧠 نتيجة الذكاء الاصطناعي:\n", result_text[:1000])

                # استخراج JSON من النتيجة
                json_match = re.search(r"\{.*\}", result_text, re.S)
                if json_match:
                    data = json.loads(json_match.group(0))
                    scores = data.get("scores", [])
                    comment = data.get("overall_comment", "— لا توجد ملاحظات عامة —")

                    df = pd.DataFrame(scores)
                    for col in ["criterion", "score", "reason", "ai_question"]:
                        if col not in df.columns:
                            df[col] = "—"

                    # تحويل القيم الرقمية وحساب النسبة
                    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
                    overall = df["score"].mean() / 4  # من 0 إلى 1

                    results.append(
                        {"file": f.name, "overall": overall, "comment": comment}
                    )
                    details[f.name] = df
                else:
                    st.warning(f"⚠️ النموذج لم يُرجع JSON صالح للملف: {f.name}")

            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء تقييم الملف {f.name}: {e}")

    # ===== تحويل النتائج إلى DataFrame =====
    if results:
        ranked = pd.DataFrame(results).sort_values("overall", ascending=False)
        ranked.reset_index(drop=True, inplace=True)
        return ranked, details
    else:
        st.warning("⚠️ لم يتم تقييم أي من العروض.")
        return pd.DataFrame(), {}
