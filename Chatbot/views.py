from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .utils import get_groq_response

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
        data = json.loads(request.body)
        user_message = data.get('message')
        language = data.get('language', 'English')
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Build Context
        context_str = ""
        if request.user.is_authenticated:
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
            context_str = "User is not logged in."

        bot_response = get_groq_response(user_message, language, context=context_str)
        return JsonResponse({'response': bot_response})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
