import os
import django
import dotenv
import random

# Setup django
dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from companies.models import Company
from jobs.models import Job

User = get_user_model()

def run_seed():
    print("Seeding data...")
    
    # Ensure admin user exists for ownership
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("Admin user not found, create superuser first.")
        return

    # Create Companies
    companies_data = [
        {"name": "TechAfrica", "location": "Accra, Ghana", "slug": "tech-africa"},
        {"name": "Nairobi Ventures", "location": "Nairobi, Kenya", "slug": "nairobi-ventures"},
        {"name": "Lagos Fintech", "location": "Lagos, Nigeria", "slug": "lagos-fintech"},
        {"name": "Remote Co", "location": "Remote", "slug": "remote-co"},
    ]

    companies = []
    for c_data in companies_data:
        company, created = Company.objects.get_or_create(
            slug=c_data['slug'],
            defaults={
                'name': c_data['name'],
                'location': c_data['location'],
                'owner': admin_user,
                'description': f"A leading tech company based in {c_data['location']}."
            }
        )
        companies.append(company)

    # Create Jobs
    job_titles = ["Software Engineer", "Frontend Developer", "Backend Developer", "Product Manager", "Data Scientist"]
    
    for i in range(20):
        company = random.choice(companies)
        title = random.choice(job_titles)
        Job.objects.create(
            title=f"{title} - {company.name}",
            company=company,
            location=company.location,
            job_type=random.choice(Job.JobType.values),
            salary_range="$50k - $100k",
            description="We are looking for a talented individual to join our team...",
            requirements="React, Django, Python...",
            is_remote=(company.location == "Remote")
        )

    print("Seeding complete! Created 4 companies and 20 jobs.")

if __name__ == '__main__':
    run_seed()
