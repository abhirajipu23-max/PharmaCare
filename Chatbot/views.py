from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .utils import get_groq_response, extract_text_from_image, generate_audio, transcribe_audio

# Create your views here.
def home(request):
    return render(request, 'chatbot.html')

def product_list(request):
    return render(request, 'chatbot.html')

def product_detail(request, slug):
    return render(request, 'chatbot.html')

@csrf_exempt
@require_POST
def chat_api(request):
    try:
        # Check if it's a multipart request (file upload) or JSON
        if request.content_type.startswith('multipart/form-data'):
            user_message = request.POST.get('message')
            language = request.POST.get('language', 'English')
            uploaded_file = request.FILES.get('file')
        else:
            data = json.loads(request.body)
            user_message = data.get('message')
            language = data.get('language', 'English')
            uploaded_file = None
        
        if not user_message and not uploaded_file:
            return JsonResponse({'error': 'Message or file is required'}, status=400)
        
        # Build Context
        context_str = ""
        
        # Handle File Upload
        if uploaded_file:
            try:
                file_content = ""
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                if file_ext == 'txt':
                    file_content = uploaded_file.read().decode('utf-8')
                elif file_ext == 'pdf':
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        file_content += page.extract_text() + "\n"
                elif file_ext in ['jpg', 'jpeg', 'png']:
                    # Reset file pointer if needed, though for uploaded_file it's usually at 0
                    # uploaded_file.seek(0) 
                    file_bytes = uploaded_file.read()
                    file_content = extract_text_from_image(file_bytes)
                
                if file_content:
                    context_str += f"\n\nUSER UPLOADED FILE CONTENT ({uploaded_file.name}):\n{file_content}\n"
                else:
                     context_str += f"\n\nUSER UPLOADED FILE ({uploaded_file.name}) but could not extract text.\n"
            except Exception as e:
                context_str += f"\n\nError reading uploaded file: {str(e)}\n"

        # Determine User Identifier (User ID or Session ID)
        from .models import ChatMessage
        
        user_id = None
        session_id = None
        
        if request.user.is_authenticated:
            user_id = request.user
            name_to_use = request.user.first_name if request.user.first_name else request.user.username
            context_str += f"User: {name_to_use}\n"
            
            # Get Cart
            from cart.models import Cart
            carts = Cart.objects.filter(user=request.user)
            if carts.exists():
                cart = carts.last()
                items = cart.items.all()
                if items:
                    context_str += "Current Cart:\n"
                    for item in items:
                        context_str += f"- {item.quantity}x {item.product.name} (${item.get_subtotal()})\n"
                    context_str += f"Cart Total: ${cart.get_total()}\n"
                else:
                    context_str += "Current Cart: Empty\n"
            
            # Get Orders
            # Assuming Order model has related_name='order_set' or similar (default)
            recent_orders = request.user.order_set.all().order_by('-created_at')[:3]
            if recent_orders:
                context_str += "Recent Orders:\n"
                for order in recent_orders:
                    context_str += f"- Order #{order.id}: {order.status} (${order.total_price}) - {order.created_at.strftime('%Y-%m-%d')}\n"
            else:
                context_str += "Recent Orders: None\n"
        else:
            # Check for session key or create one
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key
            context_str += "User is not logged in."

        # If there's no user message but there is a file, create a default message
        if not user_message and uploaded_file:
            user_message = f"I have uploaded a file named {uploaded_file.name}. Please analyze it, summarize its key points, and suggest 3 medical or health-related follow-up questions I can ask about it."

        # Save User Message to DB
        ChatMessage.objects.create(
            user=user_id,
            session_id=session_id,
            message=user_message,
            role='user'
        )

        # Retrieve Conversation History (Last 10 messages)
        if user_id:
            previous_messages = ChatMessage.objects.filter(user=user_id).order_by('-created_at')[:10]
        else:
            previous_messages = ChatMessage.objects.filter(session_id=session_id).order_by('-created_at')[:10]
            
        # Convert to Groq API format (reverse because we fetched latest first)
        history = []
        for msg in reversed(previous_messages):
             # Skip the just added message to avoid duplication if we handle it differently, 
             # but here we just fetching all. 
             # Wait, we just inserted the user message. So it will be in `previous_messages`.
             # We should exclude the current message from history because `get_groq_response` takes current message as separate arg.
             if msg.message == user_message and msg.role == 'user' and msg == previous_messages[0]:
                 continue
             history.append({"role": msg.role, "content": msg.message})

        bot_response = get_groq_response(user_message, language, context=context_str, history=history)
        
        # Save Assistant Response to DB
        ChatMessage.objects.create(
            user=user_id,
            session_id=session_id,
            message=bot_response,
            role='assistant'
        )
        
        return JsonResponse({'response': bot_response})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def text_to_speech_api(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)
            
        audio_base64 = generate_audio(text)
        
        if audio_base64:
            return JsonResponse({'audio': audio_base64})
        else:
            return JsonResponse({'error': 'Failed to generate audio'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def transcribe_api(request):
    try:
        if 'audio' not in request.FILES:
            return JsonResponse({'error': 'No audio file provided'}, status=400)
            
        audio_file = request.FILES['audio']
        
        # Save to temporary file
        # Used named temp file but need to close it so other process can read/open it if needed,
        # or just correct extension for sarvam to detect type?
        # Sarvam likely needs extension.
        import tempfile
        import shutil
        import os
        
        # Create a temp file with correct extension (e.g. .wav or .webm depending on frontend)
        # We will assume frontend sends blob with simple filename or we default to .webm
        ext = os.path.splitext(audio_file.name)[1]
        if not ext:
            ext = ".webm" # Common for browser audio recording
            
        # Get language mapping
        language_map = {
            'Hindi': 'hi-IN',
            'English': 'en-IN',
            'Hinglish': 'hi-IN', # Use Hindi model for Hinglish as it often handles code-mixing well, or fallback to 'unknown'
        }
        
        selected_language = request.POST.get('language', 'English')
        language_code = language_map.get(selected_language, 'unknown')
            
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_audio_path = temp_audio.name
            
        # Transcribe
        text = transcribe_audio(temp_audio_path, language_code=language_code)
        
        # Cleanup input file
        try:
            os.remove(temp_audio_path)
        except:
            pass
            
        if text:
            return JsonResponse({'text': text})
        else:
            return JsonResponse({'error': 'Transcription failed'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
