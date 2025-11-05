import random
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# Import your models - adjust these imports based on your app structure
from therapist.models import TherapistAddress, Services, BankDetails, TherapistStatus
from customer.models import CustomerAddress
from api.models import Pictures

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with dummy data - 10 customers and 100 therapists'
    
    def __init__(self):
        super().__init__()
        self.fake = Faker()
        
        # Service types with price ranges
        self.service_options = {
            'foot': (30, 80),
            'thai': (60, 120),
            'oil': (50, 100),
            'aroma': (70, 150),
            '4_hands_oil': (120, 250),
            'pedicure': (25, 60),
            'nails': (20, 50),
            'hair': (40, 90)
        }
        
        self.banks = [
            "First National Bank", "Chase Bank", "Bank of America", "Wells Fargo", 
            "Citibank", "US Bank", "PNC Bank", "Capital One", "TD Bank", "Regions Bank"
        ]
        
        # Address options for customers
        self.customer_address_names = [
            "Home", "Work", "Office", "Apartment", "Studio", "Friend", "Family", "Gym"
        ]
        
        # Country codes (focusing on common ones)
        self.country_codes = [91, 1, 44, 33, 49, 81, 86, 61, 55, 52]
    
    def generate_phone_data(self):
        """Generate country code and phone number"""
        country_code = random.choice(self.country_codes)
        if country_code == 91:  # India
            number = random.randint(7000000000, 9999999999)
        elif country_code == 1:  # US/Canada
            number = random.randint(2000000000, 9999999999)
        else:
            number = random.randint(100000000, 9999999999)
        
        return country_code, number
    
    def generate_coordinates(self):
        """Generate realistic latitude and longitude"""
        lat = round(random.uniform(-90, 90), 6)
        lng = round(random.uniform(-180, 180), 6)
        return str(lat), str(lng)
    
    def generate_swift_code(self):
        """Generate realistic SWIFT code"""
        country_codes = ['US', 'IN', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP']
        country = random.choice(country_codes)
        bank_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
        location = random.choice(['33', '44', '22', '11'])
        return f"{bank_code}{country}{location}"
    
    def create_customer(self):
        """Create a customer following the exact format"""
        country_code, number = self.generate_phone_data()
        
        customer_data = {
            "name": self.fake.name(),
            "email": self.fake.email(),
            "country_code": country_code,
            "number": number,
            "gender": random.choice(['male', 'female', 'other', 'prefer_not_to_say']),
            "role": "customer",
            "consent": True,
            "password": "123",
            "verification_method": "email"
        }
        
        customer = User.objects.create_user(
            name=customer_data["name"],
            email=customer_data["email"],
            country_code=str(customer_data["country_code"]),
            number=str(customer_data["number"]),
            password=customer_data["password"],
            gender=customer_data["gender"],
            role=customer_data["role"],
            consent=customer_data["consent"],
            verification_status=True
        )
        
        num_addresses = random.randint(1, 3)
        for _ in range(num_addresses):
            lat, lng = self.generate_coordinates()
            address_data = {
                "name": random.choice(self.customer_address_names),
                "address": f"{self.fake.street_address()}, {self.fake.city()}",
                "latitude": lat,
                "longitude": lng
            }
            CustomerAddress.objects.create(
                user=customer,
                name=address_data["name"],
                address=address_data["address"],
                latitude=Decimal(address_data["latitude"]),
                longitude=Decimal(address_data["longitude"])
            )
        
        return customer
    
    def create_therapist(self):
        """Create a therapist following the exact format"""
        country_code, number = self.generate_phone_data()
        
        therapist_data = {
            "name": self.fake.name(),
            "email": self.fake.email(),
            "country_code": country_code,
            "number": number,
            "gender": random.choice(['male', 'female', 'other']),
            "role": "therapist",
            "consent": True,
            "password": "123",
            "verification_method": "email"
        }
        
        therapist = User.objects.create_user(
            name=therapist_data["name"],
            email=therapist_data["email"],
            country_code=str(therapist_data["country_code"]),
            number=str(therapist_data["number"]),
            password=therapist_data["password"],
            gender=therapist_data["gender"],
            role=therapist_data["role"],
            consent=therapist_data["consent"],
            verification_status=True
        )
        
        # Address
        lat, lng = self.generate_coordinates()
        address_data = {
            "address": f"{self.fake.street_address()}, {self.fake.city()}",
            "service_radius": str(round(random.uniform(5.0, 25.0), 2)),
            "latitude": lat,
            "longitude": lng
        }
        TherapistAddress.objects.create(
            user=therapist,
            address=address_data["address"],
            service_radius=Decimal(address_data["service_radius"]),
            latitude=Decimal(address_data["latitude"]),
            longitude=Decimal(address_data["longitude"])
        )
        
        # Services
        num_services = random.randint(2, 4)
        selected_services = random.sample(list(self.service_options.keys()), num_services)
        services_data = {"services": {}}
        for service in selected_services:
            min_price, max_price = self.service_options[service]
            price = round(random.uniform(min_price, max_price), 2)
            services_data["services"][service] = price
        Services.objects.create(
            user=therapist,
            services=services_data["services"]
        )
        
        # Bank details
        bank_data = {
            "bank_name": random.choice(self.banks),
            "account_number": str(random.randint(100000000, 999999999)),
            "swift_code": self.generate_swift_code()
        }
        BankDetails.objects.create(
            user=therapist,
            bank_name=bank_data["bank_name"],
            account_number=bank_data["account_number"],
            swift_code=bank_data["swift_code"]
        )
        
        # Therapist status (updated to match new model)
        TherapistStatus.objects.create(
            user=therapist,
            status=random.choice(['available', 'unavailable'])
        )
        
        # Pictures
        Pictures.objects.create(
            user=therapist,
            profile_picture=self.fake.image_url(width=400, height=400),
            more_pictures=[
                self.fake.image_url(width=400, height=300) 
                for _ in range(random.randint(1, 4))
            ],
            certificate=self.fake.image_url(width=800, height=600) if random.choice([True, False]) else None,
            national_id=self.fake.image_url(width=600, height=400) if random.choice([True, False]) else None
        )
        
        return therapist
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))
        
        # Clear existing data
        self.stdout.write('Clearing existing customer and therapist data...')
        User.objects.filter(role__in=['customer', 'therapist']).delete()
        
        # Create customers
        self.stdout.write('Creating 10 customers...')
        customers = []
        for i in range(10):
            customer = self.create_customer()
            customers.append(customer)
            self.stdout.write(f'Created customer {i+1}: {customer.name} (Email: {customer.email})')
        
        # Create therapists
        self.stdout.write('Creating 100 therapists...')
        therapists = []
        for i in range(100):
            therapist = self.create_therapist()
            therapists.append(therapist)
            if (i + 1) % 10 == 0:
                self.stdout.write(f'Created {i+1} therapists...')
        
        # Create admin user if it doesn't exist
        if not User.objects.filter(email='admin@example.com').exists():
            self.stdout.write('Creating admin user...')
            admin = User.objects.create_superuser(
                name='Admin User',
                email='admin@example.com',
                password='admin123'
            )
        
        # Sample output omitted for brevity
        self.stdout.write(self.style.SUCCESS('=== POPULATION COMPLETE ==='))
