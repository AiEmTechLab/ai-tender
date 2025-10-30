import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def show_chatbot_page():
    st.title("💬 الشاتبوت الذكي لمناقشة العروض")

    if "_offers" not in st.session_state:
        st.warning("يرجى رفع العروض أولاً من الصفحة الرئيسية.")
        return

    st.markdown("🧠 يمكنك مناقشة نتائج التقييم أو الاستفسار عن محتوى أي عرض.")
    user_input = st.text_input("🗨️ اكتب سؤالك هنا:")

    if user_input:
        with st.spinner("🤔 جاري التفكير..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "أنت مساعد ذكي متخصص في تحليل العروض ومقارنتها."},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=400,
                    temperature=0.4
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"حدث خطأ أثناء المحادثة: {e}")
