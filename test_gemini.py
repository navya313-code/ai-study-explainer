from services.gemini_service import generate_explanation

text = generate_explanation("Photosynthesis", "simple", "English")
print(text)