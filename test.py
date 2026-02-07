import google.generativeai as genai

# Configure with your API key
genai.configure(api_key="AIzaSyC29dnfHtmIDTrnVtemXEctaBC8X68TAiU")

# List available models
for model in genai.list_models():
    print(f"Name: {model.name}")
    print(f"Supported methods: {model.supported_generation_methods}")
    print("-" * 50)