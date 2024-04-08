import os
import django
from main_app.models import CustomUser

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
            'password': password
        })
    return fake_users

def write_fake_data_to_file(fake_users, filename):
    with open(filename, 'w') as file:
        for user in fake_users:
            file.write(f"Username: {user['username']}\n")
            file.write(f"Email: {user['email']}\n")
            file.write(f"Password: {user['password']}\n")
            file.write("\n")  # Add a newline to separate users

def write_fake_data_to_database(fake_users):
    for user_data in fake_users:
        user = CustomUser.objects.create(
            username=user_data['username'],
            email=user_data['email']
        )
        user.set_password(get_random_string(12))  # Generate a random password and hash it
        user.save()
        
# Generate fake data
fake_users = generate_fake_data(10)  # Generate 1000 fake users

# Write fake data to a text file
write_fake_data_to_file(fake_users, 'fake_users.txt')

print("Fake data has been written to 'fake_users.txt'.")
