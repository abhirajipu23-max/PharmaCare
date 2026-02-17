
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
