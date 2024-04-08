import os
import random
import string
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Now you can import Django settings safely
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from main_app.models import CustomUser, Teacher
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def generate_fake_teachers(num_teachers):
    fake_teachers = []
    with open('fake_users.txt', 'w') as file:
        for i in range(num_teachers):
            # Generate fake first name and last name
            unique_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            first_name = "Teacher"
            last_name = generate_last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{unique_id}@qq.com"
            password = get_random_string(12)  # Generate a random password
            hashed_password = make_password(password)  # Hash the password
            # Write email and password to file
            file.write(f"Email: {email}, Password: {password}\n")
            
            fake_teachers.append({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': hashed_password,  # Include the password in the dictionary
                'gender': random.choice(['M', 'F']),
                'profile_pic': '/media/default.jpg',  # Provide a default profile picture path
                'address': 'Sample Address',
                'contact_num': '1234567890',  # Provide a default contact number
                'remark': 'Sample Remark',
                'fcm_token': ''  # Provide a default FCM token if applicable
            })
    return fake_teachers
def generate_last_name():
    # Generate a random last name
    syllables = ['bo', 'cha', 'da', 'fe', 'ga', 'hi', 'jo', 'ka', 'la', 'ma', 'na', 'pa', 'ra', 'sa', 'ta', 'va']
    last_name = ''.join(random.choices(syllables, k=random.randint(2, 3))).title()
    return last_name

# Generate fake teachers
def write_fake_data_to_database(fake_users):
    for teacher_data in fake_teachers:
        user = CustomUser.objects.create(
            first_name=teacher_data['first_name'],
            last_name=teacher_data['last_name'],
            email=teacher_data['email'],  # Use the provided password
            user_type=2,  # Assuming 2 represents the user type for teachers
            gender=teacher_data['gender'],
            profile_pic=teacher_data['profile_pic'],
            address=teacher_data['address'],
            contact_num=teacher_data['contact_num'],
            remark=teacher_data['remark'],
            fcm_token=teacher_data['fcm_token']
        )
        user.set_password(teacher_data['password'])  # Generate a random password and hash it
        user.save()
        teacher = Teacher.objects.create(
            course=None,  # Set the course if applicable
            admin=user,
            work_type="Special Teacher"  # Set the work type if applicable
        )

# Write fake teachers to the database
fake_teachers = generate_fake_teachers(1)
write_fake_data_to_database(fake_teachers)
