import os
import random
import string
import django
import csv
import pandas as pd

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Now you can import Django settings safely
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from main_app.models import CustomUser
from django.db import IntegrityError


def generate_fake_data(num_data):
    fake_data = []
    with open('fake_users.txt', 'w') as file:
        for i in range(num_data):
            # Generate fake first name and last name
            unique_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            first_name = "Student"
            last_name = generate_last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{unique_id}@qq.com"
            password = get_random_string(12)  # Generate a random password
            hashed_password = make_password(password)  # Hash the password
            # Write email and password to file
            file.write(f"Email: {email}, Password: {password}\n")

            fake_data.append({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,  # Include the password in the dictionary
                'gender': random.choice(['M', 'F']),
                'profile_pic': '/media/default.jpg',  # Provide a default profile picture path
                'address': 'Sample Address',
                'contact_num': '1234567890',  # Provide a default contact number
                'remark': 'Sample Remark',
                'fcm_token': ''  # Provide a default FCM token if applicable
            })
    return fake_data

def generate_last_name():
    # Generate a random last name
    syllables = ['bo', 'cha', 'da', 'fe', 'ga', 'hi', 'jo', 'ka', 'la', 'ma', 'na', 'pa', 'ra', 'sa', 'ta', 'va']
    last_name = ''.join(random.choices(syllables, k=random.randint(2, 3))).title()
    return last_name

def write_fake_data_to_database(fake_data):
    for teacher_data in fake_data:
        try:

            user = CustomUser.objects.create_user(
                email=teacher_data['email'],
                is_teacher=False,
                is_superuser = False,
                user_type = 3,
                first_name=teacher_data['first_name'],
                last_name=teacher_data['last_name'],
                password=teacher_data['password'],  # Use the provided password  # Assuming 2 represents the user type for data
                gender=teacher_data['gender'],
                profile_pic=teacher_data['profile_pic'],
                address=teacher_data['address'],
                contact_num=teacher_data['contact_num'],
                remark=teacher_data['remark'],
                fcm_token=teacher_data['fcm_token']
                )

        except IntegrityError:
            # Handle integrity errors, e.g., by generating a new admin_id
            print("Error")
            pass

# Generate fake data
fake_data = generate_fake_data(5)

# Write fake data to the database
# write_fake_data_to_database(fake_data)

def excel_to_csv(excel_file, csv_file):
    # Read the Excel file into a pandas DataFrame
    df = pd.read_excel(excel_file)

    # Write the DataFrame to a CSV file
    df.to_csv(csv_file, index=False)  # Set index=False to exclude row numbers from the CSV

# Specify the paths for your Excel and CSV files
excel_file = 'C:/Users/total/Desktop/开发计划.xlsx'  # Change this to the path of your Excel file
csv_file = 'output.csv'    # Change this to the desired path for your CSV file

# Convert Excel to CSV
excel_to_csv(excel_file, csv_file)

def read_csv_and_display_fields(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            print("Row:")
            for field, value in row.items():
                print(f"{field}: {value}")
            print()  # Add a newline between rows


# Assuming your CSV file is named 'data.csv', you can call the function like this:
read_csv_and_display_fields('output.csv')