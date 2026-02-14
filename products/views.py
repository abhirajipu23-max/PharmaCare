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
            
            # Groq Extraction using Vision Model
            api_key = settings.GROQ_API_KEY
            if not api_key:
                return render(request, 'products/upload_rx.html', {'error': 'System Error: Groq API Key missing. Please set GROQ_API_KEY in .env'})
            
            client = groq.Groq(api_key=api_key)
            
            # Prompt for Vision Model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Identify all medicine names in this prescription image. Return ONLY a valid JSON list of strings (e.g. [\"Medicine A\", \"Medicine B\"]). Do not include any other text or markdown formatting."
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
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="llama-3.2-90b-vision-preview",
                )
                response_content = chat_completion.choices[0].message.content.strip()
            except groq.BadRequestError as e:
                # Fallback to 11b if 90b is not available or fails
                logging.warning(f"Groq 90b vision failed, trying 11b: {e}")
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="llama-3.2-11b-vision-preview",
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
                    # Sometimes models return a dict, try to find list in it
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
            
            # Product Matching
            matched_products = []
            for med in detected_medicines:
                # Search by name (icontains)
                matches = Product.objects.filter(name__icontains=med, active=True)
                for match in matches:
                    if match not in matched_products:
                        matched_products.append(match)
            
            return render(request, 'products/rx_results.html', {
                'detected_medicines': detected_medicines,
                'matched_products': matched_products
            })

        except Exception as e:
            logging.error(f"Error processing Rx: {str(e)}")
            return render(request, 'products/upload_rx.html', {'error': f"Error processing image: {str(e)}"})

    return render(request, 'products/upload_rx.html')
