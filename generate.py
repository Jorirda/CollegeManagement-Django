import os

import django
import pandas as pd
import numpy as np
from faker import Faker
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from main_app.models import CustomUser
from django.db import IntegrityError

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')
django.setup()

# Create a Faker generator
fake = Faker()

# Define the number of samples
num_samples = 3

# Generate fake data
data = {
    'Full Name': [fake.name() for _ in range(num_samples)],
    'Email': [fake.email() for _ in range(num_samples)],
    'Home Number': [fake.phone_number() for _ in range(num_samples)],
    'Cell Number': [fake.phone_number() for _ in range(num_samples)],
    'Campus': [fake.city() for _ in range(num_samples)],
    'Grade': np.random.randint(1, 13, size=num_samples),
    'Gender': [fake.random_element(elements=('Male', 'Female')) for _ in range(num_samples)],
    'Date of Birth': [fake.date_of_birth(minimum_age=10, maximum_age=18).isoformat() for _ in range(num_samples)],
    'Address': [fake.address().replace('\n', ', ') for _ in range(num_samples)],
    'Registration Date': [fake.date_this_year().isoformat() for _ in range(num_samples)],
    'State': [fake.state() for _ in range(num_samples)],
    'Remark': ['None' for _ in range(num_samples)]  # Placeholder for remarks
}

# Create a DataFrame
df = pd.DataFrame(data)

# Specify a file path to save the Excel file
file_path = 'student_information.xlsx'

# Save DataFrame to an Excel file
df.to_excel(file_path, index=False)

print(f"Excel file generated: {file_path}")



def process_data(excel_file, is_teacher):
    try:
        df = pd.read_excel(excel_file)
        print("Dataframe loaded successfully with {} rows.".format(len(df)))
    except Exception as e:
        print(f"Failed to read Excel file: {str(e)}")
        return None  # Return early if the file cannot be processed

    fake_data = []

    if is_teacher:
        file = open('fake_users.txt', 'w')
        print("Opened file for writing teacher login information.")

    for index,row in df.iterrows():
        first_name = row['Full Name'].split()[0]
        last_name = row['Full Name'].split()[-1]
        email = row['Email']

        if is_teacher:
            password = get_random_string(12)
            hashed_password = make_password(password)
            file.write(f"Email: {email}, Password: {password}\n")
            print(f"Processed teacher {email} - login info written to file.")
        else:
            password = None
            hashed_password = None
            print(f"Processed student {email} - no login info required.")

        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': hashed_password,
            'profile_pic': '/media/default.jpg',
            'gender': row['Gender'],
            'address': row['Address'],
            'cell_number': row['Cell Number'],
            'home_number': row['Home Number'],
            'is_teacher': is_teacher,
            'user_type': 2 if is_teacher else 3,  # Assuming 2 is for teachers and 3 is for students
            'fcm_token': ''
        }

        try:
            CustomUser.objects.create_user(**user_data)
            fake_data.append(user_data)
            print(f"User {email} created and added to fake data.")
        except IntegrityError as e:
            print(f"Error: Duplicate or invalid data for email {email} - {str(e)}")

    if is_teacher:
        file.close()
        print("Teacher login file closed.")

    print("Data processing complete for", "teachers" if is_teacher else "students")
    return fake_data  # Returning fake_data could be more useful than just the file path

# Example usage
# process_data('path_to_excel_file.xlsx', is_teacher=True)