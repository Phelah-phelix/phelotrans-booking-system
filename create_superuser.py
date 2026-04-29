import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehicle_booking.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'ophelix67@gmail.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'phello254.')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Phelah')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        username=username,
        password=password,
        status='approved',
        user_type='admin'
    )
    print(f"Superuser {email} created successfully!")
else:
    print(f"Superuser {email} already exists")
