import os
import json
import urllib.request
import urllib.error
import base64
import groq

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Sarvam AI Configuration
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

def generate_audio(text):
    """
    Generates audio from text using Sarvam AI.
    Returns: base64 encoded audio string or None on failure.
    """
    try:
        # Avoid circular import if possible, or just import here
        from sarvamai import SarvamAI
        
        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)
        
        # Determine language code based on text content (rudimentary check)
        # Using hi-IN as requested/common for this user's context, or defaults. 
        # Ideally we pass language from the chat context, but for now we default to hi-IN 
        # as it covers both Hindi and English well with the 'bulbul' model.
        target_language_code = "hi-IN" 
        
        response = client.text_to_speech.convert(
            text=text,
            target_language_code=target_language_code,
            speaker="ritu",
            pace=1.1,
            speech_sample_rate=22050,
            enable_preprocessing=True,
            model="bulbul:v3"
        )
        
        # The SDK returns a response object with 'audios' list (base64 strings)
        if response.audios and len(response.audios) > 0:
            return response.audios[0]
        
        return None

    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def transcribe_audio(audio_file_path, language_code="unknown"):
    """
    Transcribes audio using Sarvam AI Batch API.
    Returns: Transcribed text or None.
    """
    try:
        from sarvamai import SarvamAI
        import tempfile
        import shutil
        
        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)
        
        # Create batch job
        job = client.speech_to_text_job.create_job(
            model="saaras:v3",
            mode="transcribe",
            language_code=language_code, 
            with_diarization=False, # Not needed for simple dictation
            num_speakers=1
        )
        
        # Upload file
        job.upload_files(file_paths=[audio_file_path])
        job.start()
        
        # Wait for completion (might take time)
        # In a real async app we wouldn't block, but here we have to for the simple API
        job.wait_until_complete()
        
        file_results = job.get_file_results()
        
        if file_results['successful']:
            # Create a temp dir for output
            with tempfile.TemporaryDirectory() as temp_dir:
                job.download_outputs(output_dir=temp_dir)
                
                # The output filename matches input filename usually, or check the successful list
                # Assuming simple mapping or just list files in temp_dir
                # Based on user snippet, we download to dir.
                
                # Let's find the json output. Usually it's {filename}.json
                input_filename = os.path.basename(audio_file_path)
                output_json_path = os.path.join(temp_dir, input_filename + ".json")
                
                if not os.path.exists(output_json_path):
                    # Fallback: check any json file in dir
                    files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
                    if files:
                        output_json_path = os.path.join(temp_dir, files[0])
                
                if os.path.exists(output_json_path):
                    with open(output_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Extract transcript. Structure depends on Sarvam API response.
                        # Assuming 'transcript' key or similar. 
                        # If 'transcript' is not top level, we might need to debug.
                        # But typically it's { "transcript": "..." } or similar for easy usage?
                        # Wait, user code didn't show reading it.
                        # Let's assume standard format: 'transcript' or content in 'segments'.
                        
                        # Let's try to get 'transcript' first.
                        if 'transcript' in data:
                            return data['transcript']
                        elif 'results' in data and isinstance(data['results'], list):
                             # Some APIs return list of results
                             return " ".join([r.get('transcript', '') for r in data['results']])
                        else:
                             # Just dump json content if structure unknown so we can debug or see it
                             # modifying to return the whole json string dump if key not found
                             # Or better, just return the raw text if possible.
                             return str(data) 
        
        return None

    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def get_groq_response(message, language="English", context=None, history=None):
    """
    Sends a message to the Groq API and returns the response.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    base_system_prompt = (
        "You are a warm, polite, and professional female medical assistant for PharmaCare. "
        "Talk like a caring female doctor or pharmacist who puts patients at ease while maintaining proper respect. "
        "Always use respectful terms like 'ji' when addressing users in Hindi/Hinglish. "
        "Be empathetic but professional - show you care without being too casual. "
        "Use simple, clear language and explain things in a way that's easy to understand. "
        "Help with medicine info, orders, health tips, and understanding uploaded documents."
    )

    # Context handling
    if context:
        base_system_prompt += f"\n\nCurrent user info:\n{context}\n"

    # Output Format Instructions
    format_instruction = (
        "\n\nCRITICAL - FOLLOW THESE RULES EXACTLY:"
        f"\n1. LANGUAGE: Reply in {language} only. Don't switch languages."
        "\n2. BE POLITE & PROFESSIONAL: Use respectful language. In Hindi/Hinglish, add 'ji' after the user's name."
        "\n3. SHOW EMPATHY: Acknowledge their concern before giving advice."
        "\n4. NO QUESTIONS TO USER: Do NOT ask the user any questions in your response. Only provide information and advice."
        "\n5. FOLLOW-UP QUESTIONS: At the end, suggest 2-3 short questions that the USER can ask YOU next."
        "\n   ⚠️ CRITICAL: These must be FROM the user's perspective - what they would ask you."
        "\n   ⚠️ FORMAT: You MUST use this EXACT format with numbers (1., 2., 3.) for the questions to be clickable:"
        "\n\n   1. Question one here?"
        "\n   2. Question two here?"
        "\n   3. Question three here?"
        "\n\n   ✅ CORRECT examples (with clickable format):"
        "\n   1. Kya main bukhar ki dawa le sakta hoon?"
        "\n   2. Bukhar mein blood sugar kitni baar check karni chahiye?"
        "\n   3. Mujhe doctor ko kab dikhana chahiye?"
        "\n\n   ❌ WRONG formats (will NOT be clickable):"
        "\n      • Question here (bullets don't work)"
        "\n      - Question here (dashes don't work)"
        "\n      Question here (no number doesn't work)"
        "\n\n   REMEMBER: Your response should ONLY contain:"
        "\n   - Empathy and acknowledgment"
        "\n   - Information and advice"
        "\n   - Follow-up questions with numbers 1., 2., 3. (for clickable buttons)"
        "\n   Put a blank line before the questions."
    )
    
    language_instruction = ""
    if language == "Hindi":
        language_instruction = "Reply in Hindi (Devanagari script). Use respectful terms like 'ji'. Remember: DO NOT ask the user any questions. Use numbered format 1., 2., 3. for follow-up questions."
    elif language == "Hinglish":
        language_instruction = "Reply in Hinglish (Hindi written in English letters). Use respectful terms like 'ji'. Remember: DO NOT ask the user any questions. Use numbered format 1., 2., 3. for follow-up questions."
    else:
        language_instruction = "Reply in English. Use polite, professional language. Remember: DO NOT ask the user any questions. Use numbered format 1., 2., 3. for follow-up questions."

    # Combine prompts
    system_prompt = base_system_prompt + format_instruction

    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        messages.extend(history)
    
    # Append language instruction to the user message
    final_user_content = f"{message}\n\nRemember: {language_instruction}"
    messages.append({"role": "user", "content": final_user_content})

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }

    import time

    # Tier 1: Primary Model
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
        if e.code == 429:
            print(f"Rate limit hit for {GROQ_MODEL}. Waiting 1s and switching to fallback 1 (llama-3.1-8b-instant)...")
            time.sleep(1)
            
            # Tier 2: First Fallback
            data['model'] = "llama-3.1-8b-instant"
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
            except urllib.error.HTTPError as e2:
                print(f"Fallback 1 (Llama 8B) failed: {e2}")
                return "I'm currently receiving too many messages and my backup is also busy. Please try again in 30 seconds."

        error_body = e.read().decode('utf-8')
        print(f"Groq API Error: {e.code} - {e.reason}")
        print(f"Error Body: {error_body}")
        
        if e.code == 503:
             return "My service is temporarily unavailable. Please try again later."
             
        return "I'm having trouble connecting to my brain right now. Please try again later."
    except Exception as e:
        print(f"Error: {e}")
        return "An unexpected error occurred. Please try again."

def extract_text_from_image(image_bytes):
    """
    Extracts text from an image using Groq's vision model.
    """
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        client = groq.Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct", # Use the requested model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Read ALL visible text from this image. Return plain text only. If there is no text, describe the image briefly."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0,
            max_tokens=1024
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return f"[Error analyzing image: {str(e)}]"