import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the secret key from the .env file
load_dotenv()

# The Gemini model we will use (if it ever stops working, this is the one line to change)
MODEL_NAME = "gemini-2.5-flash"

# Create the connection to Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def build_prompt(topic, level, language):
    """Write the instructions we send to Gemini."""
    if level == "detailed":
        style = (
            "a detailed, in-depth explanation of about 400 words, "
            "with clear paragraphs and a real-life example"
        )
    else:
        style = (
            "a simple explanation of about 150 words, using short sentences "
            "and everyday words, as if talking to a beginner"
        )

    return (
        "You are a friendly teacher helping a student.\n"
        f"Topic: {topic}\n"
        f"Write {style}.\n"
        f"Write the whole explanation in {language}.\n"
        "Start directly with the explanation. Do not begin with a greeting or an introduction.\n"
        "Use plain text only. Do not use markdown symbols such as * or #."
    )


def generate_explanation(topic, level, language):
    """Ask Gemini to explain the topic and return the text."""
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")

    prompt = build_prompt(topic, level, language)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


def build_materials_prompt(topic, explanation, language):
    """Write the instructions for creating key points, flashcards and a quiz."""
    return (
        "You are a teacher creating study material for a student.\n"
        f"Topic: {topic}\n"
        f"Here is the explanation the student just read:\n{explanation}\n\n"
        "Based on this explanation, create study material.\n"
        f"Write all the text in {language}.\n"
        "Use plain text only. Do not use markdown symbols such as * or #.\n"
        "Return ONLY valid JSON in exactly this shape:\n"
        "{\n"
        '  "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],\n'
        '  "flashcards": [{"question": "...", "answer": "..."}],\n'
        '  "quiz": [{"question": "...", "options": ["...", "...", "...", "..."], '
        '"correct_index": 0, "explanation": "..."}]\n'
        "}\n"
        "Rules: exactly 5 key points (one short sentence each), "
        "exactly 5 flashcards (a short question and a short answer), "
        "and exactly 5 quiz questions. Each quiz question has exactly 4 options, "
        "and correct_index is the position (0, 1, 2 or 3) of the right option. "
        "Vary the position of the correct answer across the questions."
    )


def check_materials(materials):
    """Make sure Gemini's reply has the shape we expect, and clean it up."""
    try:
        key_points = [str(point) for point in materials["key_points"]]

        flashcards = [
            {"question": str(card["question"]), "answer": str(card["answer"])}
            for card in materials["flashcards"]
        ]

        quiz = []
        for item in materials["quiz"]:
            options = [str(option) for option in item["options"]]
            correct_index = int(item["correct_index"])
            if len(options) != 4 or correct_index not in range(4):
                raise ValueError("Bad quiz question")
            quiz.append({
                "question": str(item["question"]),
                "options": options,
                "correct_index": correct_index,
                "explanation": str(item.get("explanation", "")),
            })
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Gemini returned study material in an unexpected format.") from error

    return {"key_points": key_points, "flashcards": flashcards, "quiz": quiz}


def generate_study_materials(topic, explanation, language):
    """Ask Gemini for key points, flashcards and a quiz, and return them as a dictionary."""
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")

    prompt = build_materials_prompt(topic, explanation, language)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    materials = json.loads(response.text)
    return check_materials(materials)