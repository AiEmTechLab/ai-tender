# app.py
import os
import streamlit as st
import pandas as pd

# ===== استيراد الوحدات =====
from modules.ui import (
    setup_language, apply_theme, render_header,
    landing_hero, dashboard_sidebar
)
from modules.extractors import parse_criteria_from_excel, extract_text_with_pages
from modules.evaluator import evaluate_offers
from modules.analyzer import analyze_sections_with_pages  # محدثة لتحليل الأقسام + الصفحات

# ===== إعداد اللغة والتصميم =====
T = setup_language()
apply_theme()
render_header(T)

# ===== المرحلة الأولى: رفع الملفات =====
if "uploaded" not in st.session_state:
    st.session_state.uploaded = False

if not st.session_state.uploaded:
    landing_hero(T)

    ex_file = st.file_uploader(
        T("📥 رفع ملف الإكسل (المعايير)", "📥 Upload Excel (criteria)"),
        type=["xlsx", "xls"]
    )
    offers = st.file_uploader(
        T("📥 رفع عروض الشركات (PDF/DOCX — متعدد)", "📥 Upload Company Offers (PDF/DOCX)"),
        type=["pdf", "docx"], accept_multiple_files=True
    )

    colA, colB, colC = st.columns([3, 1, 3])
    with colB:
        if st.button(T("ابدأ", "Start"), type="primary", use_container_width=True):
            if ex_file and offers:
                st.session_state._excel = ex_file
                st.session_state._offers = offers
                st.session_state.uploaded = True
                st.rerun()
            else:
                st.warning(T("فضلاً ارفع ملف المعايير والعروض أولاً", "Please upload criteria & offers first."))
    st.stop()

# ===== بعد الرفع: لوحة التحكم =====
mode = dashboard_sidebar(T)
criteria_df = parse_criteria_from_excel(st.session_state._excel)
criteria_list = criteria_df["criterion"].tolist()
st.markdown("<hr>", unsafe_allow_html=True)

# ============================================
# 🧠 وضع التقييم الذكي (Evaluation)
# ============================================
if mode == T("تحليل العروض بالذكاء الاصطناعي", "AI Evaluation"):
    st.subheader(T("🏆 ترتيب العروض", "🏆 Offer Ranking"))

    with st.expander(T("عرض المعايير", "Show criteria"), expanded=False):
        st.dataframe(criteria_df, width="stretch")

    if st.button(T("⚙️ تشغيل التقييم الذكي", "⚙️ Run AI Evaluation"), type="primary"):
        ranked, details = evaluate_offers(st.session_state._offers, criteria_list)
        st.session_state.results = ranked
        st.session_state.details = details
        st.success(T("✅ تم اكتمال التقييم!", "✅ Evaluation completed!"))
        st.rerun()

    if "results" in st.session_state:
        ranked = st.session_state.results.copy()
        details = st.session_state.details
        ranked[T("النسبة %", "% Score")] = (ranked["overall"] * 100).round(1)

        st.dataframe(ranked[["file", T("النسبة %", "% Score")]], width="stretch")

        best = ranked.iloc[0]
        st.markdown(
            f"✅ **{T('أفضل عرض','Best Offer')} →** {best['file']} "
            f"<span style='color:green;font-weight:bold;'>({best[T('النسبة %','% Score')]}%)</span>",
            unsafe_allow_html=True,
        )

        st.markdown(T("### الشفافية لكل عرض", "### Transparency per Offer"))
        top_n = st.slider(
            T("اعرض تفاصيل لأفضل N عروض", "Show details for top N offers"),
            min_value=1, max_value=len(ranked), value=min(3, len(ranked))
        )
        for i, r in ranked.head(top_n).iterrows():
            fname = r["file"]
            with st.expander(f"{T('تفاصيل العرض:','Details for:')} {fname}", expanded=False):
                df_sc = details[fname].copy()
                df_sc["تحويل (0..1)"] = ((df_sc["score"].astype(float) - 1) / 3).round(3)
                st.dataframe(
                    df_sc[["criterion", "score", "تحويل (0..1)", "reason", "ai_question"]],
                    width="stretch"
                )
                st.caption(f"{T('المجموع المعياري (0..1):','Weighted Score (0..1):')} {r['overall']:.3f}")
    else:
        st.info(T("اضغط الزر لتشغيل التقييم.", "Click the button to run evaluation."))

# ============================================
# 🧭 وضع تحليل الأقسام (Topic Explorer)
# ============================================
elif mode == T("تحليل المواضيع", "Topic Explorer"):
    st.subheader(T("🧭 تحليل الأقسام الرئيسية", "🧭 Section Analyzer"))
    offers = st.session_state._offers

    # 🚀 زر التحليل الجديد
    if st.button(T("🔎 تحليل الأقسام داخل العروض", "🔎 Analyze Sections in Offers"), type="primary"):
        topics_data = {}
        for offer in offers:
            st.markdown(f"📂 **جاري تحليل العرض:** {offer.name}")

            doc_payload = extract_text_with_pages(offer)  # 🧩 استخراج النصوص مع الصفحات
            sections = analyze_sections_with_pages(doc_payload)  # 🧠 تحليل السحابي عبر Groq
            topics_data[offer.name] = sections

        st.session_state.topics = topics_data
        st.success(T("✅ تم تحليل جميع العروض واستخراج الأقسام.", "✅ All proposals analyzed successfully."))

    # 📖 عرض النتائج
    if "topics" in st.session_state and st.session_state.topics:
        offers_names = list(st.session_state.topics.keys())
        selected_offer = st.selectbox(T("اختر عرضًا:", "Select proposal:"), offers_names)

        if selected_offer:
            df = pd.DataFrame(st.session_state.topics[selected_offer])
            if not df.empty:
                section_names = df["section"].dropna().tolist()
                section = st.selectbox(T("اختر قسمًا:", "Choose section:"), section_names)

                if section:
                    row = df[df["section"] == section].iloc[0]
                    st.markdown(f"## 🟣 {row['section']}")
                    st.markdown(f"**{T('صفحة البداية','Start Page')}:** {row.get('start_page', 1)}")
                    st.markdown(f"**{T('ملخص','Summary')}:** {row['summary']}")
                    st.markdown("---")

                    st.markdown("#### 📝 " + T("النص الكامل", "Full Content"))
                    st.markdown(
                        f"<div style='background:#f9f9f9;padding:16px;border:1px solid #e6e6e6;"
                        f"border-radius:10px;white-space:pre-wrap;direction:auto;text-align:justify;"
                        f"font-family:Tajawal,Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.7;'>"
                        f"{row['content']}</div>",
                        unsafe_allow_html=True,
                    )

                    st.download_button(
                        label=T("⬇️ تنزيل نص القسم", "⬇️ Download section text"),
                        data=row["content"].encode("utf-8"),
                        file_name=f"{selected_offer}_{row['section']}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
            else:
                st.warning(T("❌ لا توجد أقسام لهذا العرض.", "❌ No sections found for this proposal."))
    else:
        st.info(T("اضغط الزر لتحليل العروض.", "Click the button to analyze proposals."))

# ============================================
# 💬 وضع الشاتبوت
# ============================================
elif mode == T("الشاتبوت", "Chatbot"):
    st.subheader(T("💬 الشاتبوت", "💬 Chatbot"))
    st.info(T(
        "سيتاح قريبًا دردشة ذكية لمناقشة تفاصيل العروض والأسئلة المرتبطة بها.",
        "A chat assistant will soon be available to discuss proposal details and insights."
    ))
