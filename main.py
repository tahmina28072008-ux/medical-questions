import os
import json
import traceback
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# -------------------------------
# Gemini API Configuration
# -------------------------------
# Use an empty string for the API key in the code.
# The runtime environment on Google Cloud Run will provide it.
# The API key will be passed as a query parameter, not a header.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyANRWJ2Xmiz7I54kqJrjCOOV2-nrwRgQGw")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"

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
    Uses Gemini API to answer medical questions with a disclaimer.
    """
    try:
        # Create a system instruction that includes the safety disclaimer.
        system_instruction = {
            "parts": [{
                "text": "You are a helpful and safe medical information assistant. Provide accurate medical information for educational purposes only. Always include a clear disclaimer that the information is not a substitute for professional medical advice, diagnosis, or treatment. Never provide a diagnosis or recommend a treatment."
            }]
        }

        # Create the user's prompt.
        user_prompt = {
            "parts": [{
                "text": question
            }]
        }

        # Construct the payload for the Gemini API call
        payload = {
            "systemInstruction": system_instruction,
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": question}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 300,
            }
        }
        
        # Add the API key to the request URL as a query parameter.
        api_url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"

        # Make the API request
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # Extract the assistant's answer from the new API response structure.
        answer = data['candidates'][0]['content']['parts'][0]['text']
        return answer.strip()

    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request failed: {e}")
        return "Sorry, I couldn't connect to the information service. Please try again later."
    except Exception as e:
        print(f"❌ Error generating Gemini answer: {e}")
        traceback.print_exc()
        return "Sorry, I couldn't generate an answer at the moment. Please try again later."


# -------------------------------
# Main entry
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 8000)))
