from apps.curricula.models import Curriculum
from .models import Department

def recalculate_department_hours(department_id: int):
    """
    Recalculates the total assigned hours (lecture, practice, laboratory, seminar)
    for a specific department by iterating through all curricula and their courses.
    Updates the Department instance directly.
    """
    try:
        department = Department.objects.get(pk=department_id)
    except Department.DoesNotExist:
        print(f"Warning: Department with ID {department_id} not found for recalculation.")
        return # Department doesn't exist, nothing to calculate

    total_lecture = 0
    total_practice = 0
    total_laboratory = 0
    total_seminar = 0

    curricula = Curriculum.objects.filter(data__isnull=False) # Only check curricula with data

    for curriculum in curricula:
        if not isinstance(curriculum.data, dict):
            continue # Skip if data is not a dictionary

        mandatory_courses = curriculum.data.get('mandatory_courses', [])
        selective_courses = curriculum.data.get('selective_courses', [])

        # Process both mandatory and selective courses/slots
        for item in mandatory_courses + selective_courses:
            if isinstance(item, dict) and item.get('department_id') == department_id:
                hours_data = item.get('hours', {})
                if isinstance(hours_data, dict):
                    total_lecture += int(hours_data.get('lecture', 0) or 0)
                    total_practice += int(hours_data.get('practice', 0) or 0)
                    total_laboratory += int(hours_data.get('laboratory', 0) or 0)
                    total_seminar += int(hours_data.get('seminar', 0) or 0)

    # Update the department instance
    department.total_lecture_hours = total_lecture
    department.total_practice_hours = total_practice
    department.total_laboratory_hours = total_laboratory
    department.total_seminar_hours = total_seminar
    department.save(update_fields=[
        'total_lecture_hours', 
        'total_practice_hours', 
        'total_laboratory_hours', 
        'total_seminar_hours'
    ])
    print(f"Successfully recalculated hours for Department ID {department_id}") 