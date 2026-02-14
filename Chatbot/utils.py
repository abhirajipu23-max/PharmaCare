import os
import json
import urllib.request
import urllib.error

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

def get_groq_response(message, language="English", context=None):
    """
    Sends a message to the Groq API and returns the response.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    system_prompt = "You are a helpful assistant for a pharmacy website called PharmaCare. You help users with medicine information, order tracking, and health advice. Keep responses concise and helpful."
    
    if context:
        system_prompt += f"\n\nCURRENT USER CONTEXT:\n{context}\nUse this information to answer user questions about their orders, cart, or account."

    if language == "Hindi":
        system_prompt += " IMPORTANT: Reply in Hindi (Devanagari script)."
    elif language == "Hinglish":
        system_prompt += " IMPORTANT: Reply in Hinglish (Hindi written in English script). Mix English and Hindi keywords naturally."
    else:
        system_prompt += " IMPORTANT: Reply in English."

    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        req = urllib.request.Request(
            GROQ_API_URL, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Groq API Error: {e.code} - {e.reason}")
        print(f"Error Body: {error_body}")
        return "I'm having trouble connecting to my brain right now. Please try again later."
    except Exception as e:
        print(f"Error: {e}")
        return "An unexpected error occurred. Please try again."
