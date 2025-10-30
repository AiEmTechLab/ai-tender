# modules/router.py
import streamlit as st

MODES = {
    "ai": ("تحليل العروض بالذكاء الاصطناعي", "AI Evaluation"),
    "topics": ("تحليل المواضيع", "Topic Explorer"),
    "chat": ("الشاتبوت", "Chatbot"),
}

def set_mode(mode_key: str):
    st.session_state.mode = mode_key

def get_mode_label(_, key):
    ar, en = MODES[key]
    return _(en, ar)

def ensure_uploads():
    return st.session_state.get("uploaded", False) and \
           "_excel" in st.session_state and "_offers" in st.session_state
