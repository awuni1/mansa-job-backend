import os
import django
import dotenv

# Setup django
dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from companies.models import Company
from jobs.models import Job

User = get_user_model()

def verify():
    print("Verifying database connection...")
    try:
        user_count = User.objects.count()
        company_count = Company.objects.count()
        job_count = Job.objects.count()
        print(f"Connection Successful!")
        print(f"Users: {user_count}")
        print(f"Companies: {company_count}")
        print(f"Jobs: {job_count}")
    except Exception as e:
        print(f"Verification Failed: {e}")

if __name__ == '__main__':
    verify()
