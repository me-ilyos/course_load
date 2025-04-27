import random
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import User
from apps.departments.models import Department
from apps.professors.models import Professor


class Command(BaseCommand):
    help = 'Creates dummy users, departments, and professors with Marvel and DC character names'

    def handle(self, *args, **kwargs):
        # Create dummy data within a transaction
        with transaction.atomic():
            self.create_departments()
            self.create_academic_admin()
            self.create_professors()
            self.assign_department_heads()

        self.stdout.write(self.style.SUCCESS('Successfully created dummy data!'))

    def create_departments(self):
        """Create departments"""
        departments_data = [
            {'title': 'Computer Science', 'code': 'CS'},
            {'title': 'Electrical Engineering', 'code': 'EE'},
            {'title': 'Mechanical Engineering', 'code': 'ME'},
            {'title': 'Physics', 'code': 'PHY'},
            {'title': 'Mathematics', 'code': 'MATH'},
            {'title': 'Chemistry', 'code': 'CHEM'},
            {'title': 'Biology', 'code': 'BIO'},
        ]

        for dept_data in departments_data:
            Department.objects.create(
                title=dept_data['title'],
                code=dept_data['code']
            )
            self.stdout.write(f"Created department: {dept_data['title']}")

    def create_academic_admin(self):
        """Create academic admin user"""
        admin_user = User.objects.create_user(
            username='nick.fury',
            email='nick.fury@shield.edu',
            password='103203303A',
            first_name='Nick',
            last_name='Fury',
            user_type=User.ACADEMIC_ADMIN
        )
        self.stdout.write(f"Created academic admin: {admin_user.get_full_name()}")

    def create_professors(self):
        """Create professor users with Marvel and DC character names"""
        # Marvel characters
        marvel_professors = [
            {'first_name': 'Tony', 'last_name': 'Stark', 'username': 'tony.stark', 'email': 'tony.stark@marvel.edu', 'title': 'Associate Professor', 'dept_code': 'EE', 'employment': 1.0, 'has_degree': True},
            {'first_name': 'Bruce', 'last_name': 'Banner', 'username': 'bruce.banner', 'email': 'bruce.banner@marvel.edu', 'title': 'Professor', 'dept_code': 'PHY', 'employment': 0.75, 'has_degree': True},
            {'first_name': 'Steve', 'last_name': 'Rogers', 'username': 'steve.rogers', 'email': 'steve.rogers@marvel.edu', 'title': 'Assistant Professor', 'dept_code': 'PHY', 'employment': 1.0, 'has_degree': False},
            {'first_name': 'Natasha', 'last_name': 'Romanoff', 'username': 'natasha.romanoff', 'email': 'natasha.romanoff@marvel.edu', 'title': 'Lecturer', 'dept_code': 'CS', 'employment': 0.5, 'has_degree': False},
            {'first_name': 'Thor', 'last_name': 'Odinson', 'username': 'thor.odinson', 'email': 'thor.odinson@marvel.edu', 'title': 'Professor', 'dept_code': 'MATH', 'employment': 1.25, 'has_degree': True},
            {'first_name': 'Peter', 'last_name': 'Parker', 'username': 'peter.parker', 'email': 'peter.parker@marvel.edu', 'title': 'Research Associate', 'dept_code': 'BIO', 'employment': 0.5, 'has_degree': False},
            {'first_name': 'Stephen', 'last_name': 'Strange', 'username': 'stephen.strange', 'email': 'stephen.strange@marvel.edu', 'title': 'Professor', 'dept_code': 'CHEM', 'employment': 1.0, 'has_degree': True},
        ]

        # DC characters
        dc_professors = [
            {'first_name': 'Bruce', 'last_name': 'Wayne', 'username': 'bruce.wayne', 'email': 'bruce.wayne@dc.edu', 'title': 'Professor', 'dept_code': 'CS', 'employment': 1.5, 'has_degree': True},
            {'first_name': 'Clark', 'last_name': 'Kent', 'username': 'clark.kent', 'email': 'clark.kent@dc.edu', 'title': 'Associate Professor', 'dept_code': 'ME', 'employment': 1.0, 'has_degree': True},
            {'first_name': 'Diana', 'last_name': 'Prince', 'username': 'diana.prince', 'email': 'diana.prince@dc.edu', 'title': 'Professor', 'dept_code': 'MATH', 'employment': 1.0, 'has_degree': True},
            {'first_name': 'Barry', 'last_name': 'Allen', 'username': 'barry.allen', 'email': 'barry.allen@dc.edu', 'title': 'Assistant Professor', 'dept_code': 'PHY', 'employment': 2.0, 'has_degree': True},
            {'first_name': 'Hal', 'last_name': 'Jordan', 'username': 'hal.jordan', 'email': 'hal.jordan@dc.edu', 'title': 'Assistant Professor', 'dept_code': 'ME', 'employment': 0.75, 'has_degree': False},
            {'first_name': 'Oliver', 'last_name': 'Queen', 'username': 'oliver.queen', 'email': 'oliver.queen@dc.edu', 'title': 'Lecturer', 'dept_code': 'BIO', 'employment': 0.5, 'has_degree': False},
            {'first_name': 'Arthur', 'last_name': 'Curry', 'username': 'arthur.curry', 'email': 'arthur.curry@dc.edu', 'title': 'Associate Professor', 'dept_code': 'BIO', 'employment': 1.0, 'has_degree': True},
        ]

        all_professors = marvel_professors + dc_professors
        for i, prof_data in enumerate(all_professors):
            # Create the user first
            user = User.objects.create_user(
                username=prof_data['username'],
                email=prof_data['email'],
                password='103203303A',
                first_name=prof_data['first_name'],
                last_name=prof_data['last_name'],
                user_type=User.PROFESSOR
            )

            # Get the department
            try:
                department = Department.objects.get(code=prof_data['dept_code'])
            except Department.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Department with code {prof_data['dept_code']} does not exist. Skipping department assignment."))
                department = None

            # Create the professor profile
            Professor.objects.create(
                user=user,
                department=department,
                employee_id=f"EMP{i+1000:04d}",
                title=prof_data['title'],
                employment_type=prof_data['employment'],
                is_degree_holder=prof_data['has_degree']
            )

            self.stdout.write(f"Created professor: {user.get_full_name()} ({prof_data['title']}) in {prof_data['dept_code']} department")

    def assign_department_heads(self):
        """Assign department heads from existing professors"""
        # Get list of departments
        departments = Department.objects.all()

        # For each department, find a professor in that department with a degree and make them head
        for dept in departments:
            # Find professors in this department who have doctoral degrees
            potential_heads = Professor.objects.filter(
                department=dept,
                is_degree_holder=True
            ).select_related('user')

            if potential_heads.exists():
                # Choose one professor randomly to be department head
                head_professor = random.choice(list(potential_heads))
                
                # Update the department
                dept.department_head = head_professor.user
                dept.save()
                
                self.stdout.write(f"Assigned {head_professor.user.get_full_name()} as head of {dept.title} department") 