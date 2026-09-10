"""
app.py
------
Flask backend for MusicBot AI chatbot.
Uses Google's Gemini API (gemini-3.1-flash-lite) to answer questions,
restricted to music learning topics only via the system prompt defined
in chatbot_config.py.
"""

import os
import base64
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

from chatbot_config import SYSTEM_PROMPT, BOT_NAME

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()  # loads variables from .env into environment

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Please add it to your .env file."
    )

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYSTEM_PROMPT,
)

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    """Render the chatbot UI."""
    return render_template("index.html", bot_name=BOT_NAME)


@app.route("/chat", methods=["POST"])
def chat():
    """
    Accepts a JSON payload:
        {
            "message": "user text message",
            "image": "data:image/png;base64,....."   (optional)
        }
    Returns:
        { "reply": "bot response text" }
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    image_data_url = data.get("image")

    if not user_message and not image_data_url:
        return jsonify({"reply": "Please type a message or attach an image."}), 400

    # Build the content list sent to Gemini (text + optional image)
    content_parts = []

    if image_data_url:
        try:
            header, encoded = image_data_url.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
            image_bytes = base64.b64decode(encoded)
            content_parts.append(
                {"mime_type": mime_type, "data": image_bytes}
            )
        except Exception:
            return jsonify({"reply": "Sorry, I couldn't read that image. Please try again."}), 400

    content_parts.append(user_message if user_message else "Please look at this image.")

    try:
        response = model.generate_content(content_parts)
        reply_text = (response.text or "").strip()
        if not reply_text:
            reply_text = "Sorry, I couldn't generate a response. Please try rephrasing your question."
    except Exception as exc:
        reply_text = f"Sorry, something went wrong while contacting the AI service. ({exc})"

    return jsonify({"reply": reply_text})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
