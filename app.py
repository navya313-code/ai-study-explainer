from flask import Flask, jsonify, render_template, request, url_for

from services.gemini_service import generate_explanation, generate_study_materials
from services.murf_service import generate_audio

app = Flask(__name__)

# The languages our dropdown offers (must match the page)
ALLOWED_LANGUAGES = ["English", "Hindi", "Spanish", "French", "German"]

# Murf accepts a limited amount of text per request
MAX_AUDIO_CHARACTERS = 12000


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/study", methods=["POST"])
def study():
    # Read the data the browser sent
    data = request.get_json(silent=True) or {}

    topic = str(data.get("topic", "")).strip()
    level = data.get("level", "simple")
    language = data.get("language", "English")

    # Check the data before spending a Gemini request
    if topic == "":
        return jsonify({"error": "Please type a topic first."}), 400
    if len(topic) > 200:
        return jsonify({"error": "That topic is too long. Please keep it under 200 characters."}), 400
    if level not in ("simple", "detailed"):
        level = "simple"
    if language not in ALLOWED_LANGUAGES:
        language = "English"

    # Ask Gemini for the explanation
    try:
        explanation = generate_explanation(topic, level, language)
    except Exception as error:
        print("Gemini error:", error)
        return jsonify({"error": "Sorry, something went wrong while creating the explanation. Please try again."}), 500

    # Send the result back to the browser
    return jsonify({
        "topic": topic,
        "level": level,
        "language": language,
        "explanation": explanation
    })


@app.route("/api/materials", methods=["POST"])
def materials():
    # Read the data the browser sent
    data = request.get_json(silent=True) or {}

    topic = str(data.get("topic", "")).strip()
    explanation = str(data.get("explanation", "")).strip()
    language = data.get("language", "English")

    # Check the data before spending a Gemini request
    if topic == "" or explanation == "":
        return jsonify({"error": "A topic and an explanation are needed first."}), 400
    if len(topic) > 200:
        return jsonify({"error": "That topic is too long. Please keep it under 200 characters."}), 400
    if len(explanation) > 10000:
        return jsonify({"error": "That explanation is too long."}), 400
    if language not in ALLOWED_LANGUAGES:
        language = "English"

    # Ask Gemini for key points, flashcards and a quiz
    try:
        study_materials = generate_study_materials(topic, explanation, language)
    except Exception as error:
        print("Gemini error (materials):", error)
        return jsonify({"error": "Sorry, we couldn't create the study material this time. Please try again."}), 500

    # Send the result back to the browser
    return jsonify(study_materials)


@app.route("/api/audio", methods=["POST"])
def audio():
    # Read the data the browser sent
    data = request.get_json(silent=True) or {}

    text = str(data.get("text", "")).strip()
    language = data.get("language", "English")

    # Check the data before spending Murf characters
    if text == "":
        return jsonify({"error": "There is no text to turn into audio."}), 400
    if len(text) > MAX_AUDIO_CHARACTERS:
        return jsonify({"error": "This explanation is too long to turn into audio in one go."}), 400
    if language not in ALLOWED_LANGUAGES:
        language = "English"

    # Ask Murf to create the audio
    try:
        filename = generate_audio(text, language)
    except Exception as error:
        print("Murf error:", error)
        return jsonify({"error": "Sorry, we couldn't create the audio this time. Please try again."}), 500

    # Send back the web address of the audio file
    return jsonify({"audio_url": url_for("static", filename="audio/" + filename)})


if __name__ == "__main__":
    app.run(debug=True)