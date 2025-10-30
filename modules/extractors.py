# modules/extractors.py
import io
import hashlib
import streamlit as st
import fitz  # PyMuPDF
from docx import Document
import pandas as pd

# ============================================================
# 🔧 أدوات مساعدة
# ============================================================
def _file_bytes(file_obj) -> bytes:
    """قراءة محتوى الملف كـ bytes دون تغيير المؤشر"""
    pos = file_obj.tell()
    file_obj.seek(0)
    data = file_obj.read()
    file_obj.seek(pos)
    return data

def _hash_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()

# ============================================================
# 📄 استخراج PDF صفحة بصفحة (بدون تحريف)
# ============================================================
@st.cache_data(show_spinner=False)
def extract_pdf_pages(name: str, data: bytes, fid: str):
    """
    يعيد قائمة صفحات:
    [{"page_num": 1, "text": "..."} , ...]
    باستخدام PyMuPDF لضمان الترتيب والدقة العالية.
    """
    pages = []
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        for i, page in enumerate(doc):
            text = page.get_text("text") or ""
            pages.append({"page_num": i + 1, "text": text})
        doc.close()
    except Exception as e:
        st.error(f"❌ خطأ في قراءة PDF {name}: {e}")
    return pages

# ============================================================
# 📝 استخراج DOCX (ملف وورد)
# ============================================================
@st.cache_data(show_spinner=False)
def extract_docx_text(name: str, data: bytes, fid: str):
    """إرجاع نص DOCX كسلسلة نصية واحدة (سطر لكل فقرة)."""
    try:
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        st.error(f"❌ خطأ في قراءة DOCX {name}: {e}")
        return ""

# ============================================================
# ⚡ الدالة الرئيسية الموحّدة للاستخدام في الواجهة
# ============================================================
def extract_text_with_pages(uploaded_file):
    """
    يكتشف نوع الملف ويعيد محتواه بشكل موحد:
    PDF → {"type": "pdf", "pages": [{"page_num":1,"text":"..."}]}
    DOCX → {"type": "docx", "text": "..."}
    """
    data = _file_bytes(uploaded_file)
    fid = _hash_bytes(data)
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        pages = extract_pdf_pages(name, data, fid)
        return {"type": "pdf", "pages": pages}
    elif name.endswith(".docx"):
        text = extract_docx_text(name, data, fid)
        return {"type": "docx", "text": text}
    else:
        st.warning("⚠️ نوع الملف غير مدعوم (يرجى رفع PDF أو DOCX فقط).")
        return {"type": "unknown"}

# ============================================================
# 📊 استخراج المعايير من Excel
# ============================================================
@st.cache_data(show_spinner=False)
def parse_criteria_from_excel(xfile) -> pd.DataFrame:
    """محاولة استخراج عمود المعايير من ملف Excel"""
    try:
        xl = pd.ExcelFile(xfile)
        target = next(
            (s for s in xl.sheet_names if "Project" in s or "Evaluation" in s or "التقييم" in s),
            xl.sheet_names[0],
        )
        df = pd.read_excel(xl, sheet_name=target, header=0)
        possibles = [
            c for c in df.columns
            if any(k in str(c) for k in ["criterion","criteria","المعيار","Component","Sub-criterion"])
        ]
        rows = []
        for c in possibles:
            vals = df[c].dropna().astype(str).map(str.strip)
            for v in vals:
                if v and v.lower() not in {"nan","none"} and len(v) > 1:
                    rows.append(v)

        seen, out = set(), []
        for r in rows:
            if r not in seen:
                seen.add(r)
                out.append({"criterion": r})
        if out:
            return pd.DataFrame(out)

        defaults = [
            "جودة الحل المقترح","المنهجية الفنية","الخبرة السابقة","خطة التنفيذ",
            "فريق العمل","الابتكار في الحل","إدارة المشروع","الامتثال للمتطلبات",
        ]
        return pd.DataFrame({"criterion": defaults})

    except Exception as e:
        st.warning(f"⚠️ تعذر قراءة Excel ({e})، سيتم استخدام قائمة افتراضية.")
        defaults = [
            "جودة الحل المقترح","المنهجية الفنية","الخبرة السابقة","خطة التنفيذ",
            "فريق العمل","الابتكار في الحل","إدارة المشروع","الامتثال للمتطلبات",
        ]
        return pd.DataFrame({"criterion": defaults})
