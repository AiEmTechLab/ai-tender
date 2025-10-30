from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "humain-ai/ALLAM-7B-Instruct-preview"

print("🔹 تحميل النموذج والـ tokenizer ...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

prompt = "حلّل النص التالي واستخرج النقاط الرئيسية:\nهذا العرض الفني يوضح المنهجية المقترحة وخطة التنفيذ والنتائج المتوقعة."
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

print("🤖 يتم التوليد ...")
outputs = model.generate(**inputs, max_new_tokens=400, do_sample=True, temperature=0.7)
print("\n🧠 النتيجة:\n", tokenizer.decode(outputs[0], skip_special_tokens=True))
