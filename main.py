import os
import json
import traceback
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# -------------------------------
# Gemini API Configuration
# -------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # Store key in Cloud Run env var
GEMINI_ENDPOINT = "https://gemini.googleapis.com/v1alpha2/chat/completions"

# -------------------------------
# Webhook endpoint
@app.route('/')
def home():
    return "Webhook is running successfully!"
# -------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        print("📥 Webhook Request:", json.dumps(req, indent=2))

        # Extract 'question' parameter from Dialogflow CX
        session_params = req.get("sessionInfo", {}).get("parameters", {})
        question = session_params.get("question", "").strip()

        if not question:
            response_text = "I didn't catch your question. Please ask a medical question."
        else:
            # Call Gemini API to get answer
            response_text = generate_gemini_answer(question)

        # Construct Dialogflow CX fulfillment response
        response = {
            "fulfillment_response": {
                "messages": [{"text": {"text": [response_text]}}]
            }
        }

        return jsonify(response)

    except Exception as e:
        print(f"❌ Error in webhook: {e}")
        traceback.print_exc()
        return jsonify({
            "fulfillment_response": {
                "messages": [{"text": {"text": ["An error occurred. Please try again later."]}}]
            }
        })

# -------------------------------
# Call Gemini API
# -------------------------------
def generate_gemini_answer(question):
    """
    Uses Gemini API to answer medical questions.
    """
    try:
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gemini-1.5-turbo",  # or another Gemini model
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful and safe medical assistant. Provide accurate medical info and include a disclaimer that it's for educational purposes only."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_output_tokens": 300
        }

        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Extract the assistant's answer
        answer = data["choices"][0]["message"]["content"]
        return answer.strip()

    except Exception as e:
        print(f"❌ Error generating Gemini answer: {e}")
        traceback.print_exc()
        return "Sorry, I couldn't generate an answer at the moment. Please try again later."


# -------------------------------
# Main entry
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 8000)))
