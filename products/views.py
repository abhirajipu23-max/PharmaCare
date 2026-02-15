from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile



def home(request):
    # Fetch all active products sorted by newest first
    all_products = Product.objects.filter(active=True).order_by('-created_at')
    
    featured_products = []
    seen_categories = set()
    
    # First pass: try to get one from each category
    for product in all_products:
        if product.category_id not in seen_categories:
            featured_products.append(product)
            seen_categories.add(product.category_id)
            if len(featured_products) == 6:
                break
    
    # Second pass: fill up to 6 if needed
    if len(featured_products) < 6:
        for product in all_products:
            if product not in featured_products:
                featured_products.append(product)
                if len(featured_products) == 6:
                    break
                    
    categories = Category.objects.all()
    return render(request, 'products/home.html', {
        'featured_products': featured_products,
        'categories': categories
    })

def product_list(request):
    products = Product.objects.filter(active=True)
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    from django.core.paginator import Paginator

    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Robust AJAX detection
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.GET.get('ajax') == '1'
    )

    if is_ajax:
        return render(request, 'products/partials/product_list_chunk.html', {'products': page_obj})

    categories = Category.objects.all()
    return render(request, 'products/product_list.html', {
        'products': page_obj,
        'categories': categories,
        'query': query
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'products/product_detail.html', {'product': product})




from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer


class ProductsApi(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        product = self.get_object()
        return Response({
            "id": product.id,
            "name": product.name,
            "price": product.price,
        })

def upload_rx(request):
    import groq
    import json
    import os
    import base64
    
    if request.method == 'POST' and request.FILES.get('rx_image'):
        try:
            image_file = request.FILES['rx_image']
            
            # Read image file and encode to base64
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            api_key = settings.GROQ_API_KEY
            if not api_key:
                return render(request, 'products/upload_rx.html', {'error': 'System Error: Groq API Key missing. Please set GROQ_API_KEY in .env'})
            
            client = groq.Groq(api_key=api_key)
            
            # Improved Prompt for Vision Model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": """Analyze this prescription image and extract ONLY actual pharmaceutical medicine/drug names.
                            
IMPORTANT RULES:
- Return ONLY a valid JSON list of strings (e.g. ["Medicine A", "Medicine B"])
- ONLY include actual medicine names (like "Paracetamol", "Amoxicillin", "Metformin")
- IGNORE any non-medicine text like:
  * Instructions (e.g., "Take twice daily", "After meals")
  * Patient information (e.g., "John Doe", "Age 45")
  * Doctor information (e.g., "Dr. Smith", "License #123")
  * Dates, addresses, or clinic names
  * Non-medical terms like "Backtesting", "Paper Trading", etc.
- If no actual medicine names are found, return an empty list []

Do not include any other text or markdown formatting."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ]

            try:
                # Use Llama 4 Scout which is multimodal
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    temperature=0.1
                )
                response_content = chat_completion.choices[0].message.content.strip()
            except groq.BadRequestError as e:
                # Fallback to Maverick if Scout fails
                logging.warning(f"Llama 4 Scout failed, trying Maverick: {e}")
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                )
                response_content = chat_completion.choices[0].message.content.strip()
            
            # Clean up potential markdown code blocks
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '')
            elif response_content.startswith('```'):
                response_content = response_content.replace('```', '')

            try:
                detected_medicines = json.loads(response_content)
                if not isinstance(detected_medicines, list):
                     if isinstance(detected_medicines, dict):
                        for key, value in detected_medicines.items():
                            if isinstance(value, list):
                                detected_medicines = value
                                break
                     else:
                        detected_medicines = []
            except json.JSONDecodeError:
                detected_medicines = []
                logging.error(f"Failed to parse Groq response: {response_content}")
            
            # Additional filtering: Only keep items that might be medicine names
            # This helps filter out obvious non-medicine terms
            filtered_medicines = []
            common_non_medical = ['backtesting', 'paper trading', 'trading alerts', 'algorithmic trading', 
                                 'buy', 'sell', 'signal', 'indicator', 'strategy', 'test', 'demo']
            
            for med in detected_medicines:
                med_lower = med.lower()
                # Skip if it contains common non-medical terms
                if any(term in med_lower for term in common_non_medical):
                    continue
                # Skip very short terms (likely not medicine names)
                if len(med) < 3:
                    continue
                filtered_medicines.append(med)
            
            # Product Matching - only with filtered medicines
            matched_products = []
            for med in filtered_medicines:
                # Search by name (icontains)
                matches = Product.objects.filter(name__icontains=med, active=True)
                for match in matches:
                    if match not in matched_products:
                        matched_products.append(match)
            
            # If no medicines detected or no matches found, return false
            if not filtered_medicines or not matched_products:
                return render(request, 'products/rx_results.html', {
                    'detected_medicines': filtered_medicines if filtered_medicines else False,
                    'matched_products': False
                })
            
            return render(request, 'products/rx_results.html', {
                'detected_medicines': filtered_medicines,
                'matched_products': matched_products
            })

        except Exception as e:
            logging.error(f"Error processing Rx: {str(e)}")
            return render(request, 'products/upload_rx.html', {'error': f"Error processing image: {str(e)}"})

    return render(request, 'products/upload_rx.html')