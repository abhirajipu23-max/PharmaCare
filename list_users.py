import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mr_doctor.settings")
django.setup()

User = get_user_model()
users = User.objects.all()

print(f"Connected to Supabase! Found {users.count()} users:")
for user in users:
    print(f"- {user.username} (joined: {user.date_joined})")
