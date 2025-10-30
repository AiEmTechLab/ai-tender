# modules/ui.py
import base64
import os
import streamlit as st

ACCENT = "#5A33A4"
ACCENT_SOFT = "#8B5CF6"

def setup_language():
    """Initialize language and return translation helper _."""
    if "lang" not in st.session_state:
        st.session_state.lang = "AR"

    def _(en, ar):
        return ar if st.session_state.lang == "AR" else en

    return _

def apply_theme():
    """Global styles + set direction by language."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;600;800&display=swap');
    html, body, [class*="css"] {{
      font-family: Tajawal, system-ui, -apple-system, Segoe UI, Roboto, Arial !important;
    }}
    h1, h2, h3, h4 {{ color: {ACCENT} !important; letter-spacing: .2px; }}
    div.stButton > button {{
      background-color: {ACCENT}; color: #fff; border-radius: 10px; font-weight: 700;
    }}
    div.stButton > button:hover {{ background-color: {ACCENT_SOFT}; }}
    [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; border: 1px solid #eee; }}
    .card {{ background:#faf9ff; border:1px solid #eee; border-radius:12px; padding:14px 16px; }}
    .badge {{ display:inline-block; padding:4px 10px; border-radius:12px; background:#F3F1FF; color:{ACCENT}; font-size:12px; font-weight:700; }}
    </style>
    """, unsafe_allow_html=True)

    # Direction
    if st.session_state.lang == "AR":
        st.markdown("""
        <style>
        body { direction: rtl; text-align: right; }
        [data-testid="stHorizontalBlock"] { flex-direction: row-reverse; }
        [data-testid="stSidebarNav"] { direction: rtl; text-align: right; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        body { direction: ltr; text-align: left; }
        </style>
        """, unsafe_allow_html=True)

def render_header(_):
    """Top header: centered title + logo + transparent fixed language button (top-left)."""
    logo_path = os.path.join("assets", "Screenshot_2025-10-20_162014-removebg-preview.png")

    # ===== زر اللغة (شفاف في أعلى اليسار وثابت) =====
    st.markdown(f"""
        <style>
        .lang-btn {{
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 9999;
            background: transparent;
            border: 2px solid {ACCENT};
            color: {ACCENT};
            padding: 6px 14px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: 0.3s;
        }}
        .lang-btn:hover {{
            background: {ACCENT};
            color: white;
        }}
        </style>

        <button class="lang-btn" onclick="window.location.href='/?lang={'EN' if st.session_state.lang == 'AR' else 'AR'}'">
            {('EN' if st.session_state.lang == 'AR' else 'AR')}
        </button>
    """, unsafe_allow_html=True)

    # ===== العنوان والشعار في المنتصف =====
    title_text = _("Smart Tender Evaluation", "التقييم الذكي للعروض")

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <div style='display:flex; justify-content:center; align-items:center; gap:14px; margin-top:50px;'>
            <img src='data:image/png;base64,{logo_b64}' width='70'>
            <h1 style='margin:0; font-weight:800; color:{ACCENT}; font-size:55px;'>{title_text}</h1>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f"<h1 style='text-align:center; color:{ACCENT}; font-weight:800;'>{title_text}</h1>",
            unsafe_allow_html=True
        )


def landing_hero(_):
    """Landing screen like ChatGPT: greeting + upload area only."""
    st.markdown(f"""
    <div style="text-align:center; padding: 40px 0 10px 0;">
      <h2 style="margin:0; color:{ACCENT};">{_('Welcome to Smart Tender Evaluator', '  مرحبًا  بك في مُقيِّم العروض الذكي'  )}</h2>
      <p style="opacity:.8; margin-top:7px;">{_('Upload your criteria file & proposals to get started.',
       '💡 ابدأ برفع ملف المعايير (Excel) وعروض الشركات (PDF/DOCX)')}</p>
    </div>
    """, unsafe_allow_html=True)

def dashboard_sidebar(_):
    """Sidebar with modes, enabled only after uploads."""
    st.sidebar.header(_("لوحة التحكم", "Dashboard"))

    mode = st.sidebar.radio(
        label=_("اختر وضع العرض", "Choose a mode"),
        options=[_("تحليل العروض بالذكاء الاصطناعي","AI Evaluation"),
                 _("تحليل المواضيع","Topic Explorer"),
                 _("الشاتبوت","Chatbot")],
        index=0,
        key="dashboard_mode"  # مفتاح يثبت الاختيار
    )

    # 🔄 إذا غيّر المستخدم الاختيار — أعد تحميل الصفحة
    if "prev_mode" not in st.session_state:
        st.session_state.prev_mode = mode
    elif st.session_state.prev_mode != mode:
        st.session_state.prev_mode = mode
        st.rerun()  # <=== الحل هنا

    return mode
