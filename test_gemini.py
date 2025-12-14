import google.generativeai as genai
import os

# Configurar a API key
api_key = "AIzaSyBtKyyNZmfOjChMNV6Kqc-S6gL0OouZ2Wg"
genai.configure(api_key=api_key)

# Listar modelos disponíveis
print("Modelos disponíveis:")
for model in genai.list_models():
    print(f"- {model.name}")
    print(f"  Supported methods: {model.supported_generation_methods}")
    print()

# Tentar com diferentes nomes
models_to_try = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-pro-latest",
    "models/gemini-1.5-flash",
    "models/gemini-pro"
]

for model_name in models_to_try:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, world!")
        print(f"✅ {model_name}: {response.text[:50]}...")
        break
    except Exception as e:
        print(f"❌ {model_name}: {e}")