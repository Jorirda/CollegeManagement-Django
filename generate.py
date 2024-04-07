import os
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Now you can import Django settings safely
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string

def generate_fake_data(num_users):
    fake_users = []
    for i in range(1, num_users + 1):
        # Generate fake user data
        if i <= 26:
            # Teachers from A to Z
            username = f"Teacher {chr(64 + i)}"
        else:
            # Students from 1 to 1000
            username = f"Student {i - 26}"
        email = f"{username.lower().replace(' ', '_')}@qq.com"
        password = get_random_string(12)  # Generate a random password
        hashed_password = make_password(password)  # Hash the password
        fake_users.append({
            'username': username,
            'email': email,
            'password': hashed_password
        })
    return fake_users

# Example usage
fake_users = generate_fake_data(10)
for user in fake_users:
    print(user)
