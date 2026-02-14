import os
import groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GROQ_API_KEY')
client = groq.Groq(api_key=api_key)

try:
    models = client.models.list()
    print("Available Models:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error: {e}")
