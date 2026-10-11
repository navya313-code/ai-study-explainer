import os
import re
import uuid

import requests
from dotenv import load_dotenv

# Load the secret key from the .env file
load_dotenv()

MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_BASE_URL = "https://api.murf.ai/v1"

# Murf accepts about 3,000 characters per request, so we stay safely under that
MAX_CHUNK_CHARACTERS = 2500

# Folder where finished audio files are saved (Flask serves it from /static/audio/)
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_FOLDER = os.path.join(PROJECT_FOLDER, "static", "audio")

# Which Murf voice to use for each language (the names come from Murf's voice list).
VOICE_BY_LANGUAGE = {
    "English": "en-US-natalie",
    "Hindi": "hi-IN-shweta",
    "Spanish": "es-ES-carmen",
    "French": "fr-FR-louise",
    "German": "de-DE-lia",
}


def check_response(response):
    """Stop with a readable message if Murf says something went wrong."""
    if not response.ok:
        raise RuntimeError(f"Murf error {response.status_code}: {response.text[:300]}")


def get_voice_id(language):
    """Find the voice we use for a language."""
    voice_id = VOICE_BY_LANGUAGE.get(language)
    if voice_id is None:
        raise ValueError(f"No Murf voice is set up for {language} yet.")
    return voice_id


def list_voices():
    """Ask Murf for its list of voices."""
    if not MURF_API_KEY:
        raise RuntimeError("MURF_API_KEY is missing. Check your .env file.")

    response = requests.get(
        f"{MURF_BASE_URL}/speech/voices",
        headers={"api-key": MURF_API_KEY},
        timeout=30,
    )
    check_response(response)
    return response.json()


def split_text(text, max_chars=MAX_CHUNK_CHARACTERS):
    """Cut long text into pieces, always at the end of a sentence."""
    sentences = re.split(r"(?<=[.!?।])\s+", text.strip())

    chunks = []
    current = ""

    for sentence in sentences:
        # A single sentence that is longer than the limit has to be cut
        while len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:max_chars])
            sentence = sentence[max_chars:]

        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def generate_audio_bytes(text, voice_id):
    """Ask Murf to read one piece of text, and return the MP3 data."""
    response = requests.post(
        f"{MURF_BASE_URL}/speech/generate",
        headers={"api-key": MURF_API_KEY, "Content-Type": "application/json"},
        json={"text": text, "voiceId": voice_id, "format": "MP3"},
        timeout=60,
    )
    check_response(response)
    audio_url = response.json()["audioFile"]

    audio_response = requests.get(audio_url, timeout=60)
    check_response(audio_response)
    return audio_response.content


def generate_audio(text, language):
    """Turn text of any length into speech, save it as one MP3 file, and return the file name."""
    if not MURF_API_KEY:
        raise RuntimeError("MURF_API_KEY is missing. Check your .env file.")

    voice_id = get_voice_id(language)

    # Read each piece, then join the pieces end to end
    audio_parts = [generate_audio_bytes(chunk, voice_id) for chunk in split_text(text)]

    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    filename = uuid.uuid4().hex + ".mp3"
    with open(os.path.join(AUDIO_FOLDER, filename), "wb") as audio_file:
        for part in audio_parts:
            audio_file.write(part)

    return filename