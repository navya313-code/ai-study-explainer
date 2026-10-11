from services.murf_service import generate_audio

tests = {
    "English": "Hello! This is a short test.",
    "Hindi": "नमस्ते! यह एक छोटा परीक्षण है।",
    "Spanish": "¡Hola! Esta es una prueba corta.",
    "French": "Bonjour ! Ceci est un court test.",
    "German": "Hallo! Das ist ein kurzer Test.",
}

for language, sentence in tests.items():
    filename = generate_audio(sentence, language)
    print(language, "->", filename)