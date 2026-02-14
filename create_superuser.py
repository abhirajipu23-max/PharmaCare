import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mr_doctor.settings")
django.setup()

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    try:
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser 'admin' created successfully.")
    except Exception as e:
        print(f"Error creating superuser: {e}")
else:
    print("Superuser 'admin' already exists.")
