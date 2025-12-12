import json

with open('data.json', 'r') as file:
    data = json.load(file)

for student in data['students']:
    student_id = student['student_id']
    major = student['major']
    name = student['name']
    age = student['age']
    date = student.get('date', 'N/A')

    print(f"Student ID: {student_id}")
    print(f"Major: {major}")
    print(f"Name: {name}")
    print(f"Age: {age}")
    print(f"Date: {date}")
    print("-" * 20)
