import os
import django
import dotenv

# Setup django
dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@mansa.com', 'admin123')
    print("Superuser 'admin' created.")
else:
    print("Superuser 'admin' already exists.")
