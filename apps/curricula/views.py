import re
from django.shortcuts import render, redirect, get_object_or_404
import openpyxl
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from .models import Curriculum
from apps.departments.models import Department # Import Department model
from .forms import CurriculumForm
from django.contrib import messages
from django.urls import reverse_lazy
from .parser import extract_mandatory_courses, extract_selective_courses
import tempfile
import os
import json

# Create your views here.


class CurriculumListView(ListView):
    model = Curriculum
    template_name = 'curricula/curriculum_list.html'
    context_object_name = 'curricula'
    paginate_by = 10 # Optional: add pagination

    def get_queryset(self):
        return Curriculum.objects.all().order_by('title', 'start_year')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CurriculumForm()
        return context

def curriculum_create_view(request):
    if request.method == 'POST':
        form = CurriculumForm(request.POST, request.FILES)
        if form.is_valid():
            curriculum_instance = form.save(commit=False)

            excel_file = form.cleaned_data.get('source_excel_file')
            if excel_file:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_excel:
                        for chunk in excel_file.chunks():
                            temp_excel.write(chunk)
                        temp_excel_path = temp_excel.name
                    
                    parsed_mandatory_data = extract_mandatory_courses(temp_excel_path)
                    parsed_selective_data = extract_selective_courses(temp_excel_path)
                    curriculum_instance.data = {
                        "mandatory_courses": parsed_mandatory_data,
                        "selective_courses": parsed_selective_data
                    }
                    
                except Exception as e:
                    messages.error(request, f"Excel faylini qayta ishlashda xatolik: {e}")
                    if 'temp_excel_path' in locals() and os.path.exists(temp_excel_path):
                        os.remove(temp_excel_path)
                    return redirect(reverse_lazy('curricula:curriculum_list'))
                finally:
                    if 'temp_excel_path' in locals() and os.path.exists(temp_excel_path):
                        os.remove(temp_excel_path)
            
            curriculum_instance.save()
            messages.success(request, "O'quv rejasi muvaffaqiyatli qo'shildi.")
            return redirect(reverse_lazy('curricula:curriculum_list'))
        else:
            for field, errors in form.errors.items():
                field_label = form.fields[field].label if field in form.fields else field
                for error in errors:
                    messages.error(request, f"{field_label}: {error}")
            return redirect(reverse_lazy('curricula:curriculum_list'))
    return redirect(reverse_lazy('curricula:curriculum_list'))


def upload_excel(request):
    return render(request, 'curricula/upload_excel.html')

# Example of a function-based view if preferred for simpler cases:
# def curriculum_list_view(request):
#     curricula = Curriculum.objects.all().order_by('title', 'start_year')
#     return render(request, 'curricula/curriculum_list.html', {'curricula': curricula})

class CurriculumDetailView(DetailView):
    model = Curriculum
    template_name = 'curricula/curriculum_detail.html'
    context_object_name = 'curriculum'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curriculum = self.get_object() # Get the curriculum object
        departments = Department.objects.all().order_by('title')
        
        departments_values = list(departments.values('id', 'title', 'code'))
        context['departments_json_string'] = json.dumps(departments_values)
        context['departments_qs'] = departments

        department_map = {dept.id: dept.title for dept in departments}
        
        # Initialize overall hour totals
        overall_totals = {
            'lecture': 0,
            'practice': 0,
            'laboratory': 0,
            'seminar': 0
        }

        if curriculum.data:
            mandatory_courses = curriculum.data.get('mandatory_courses', [])
            selective_courses = curriculum.data.get('selective_courses', []) # These are slots

            course_lists_to_process = [mandatory_courses, selective_courses]

            for course_list in course_lists_to_process:
                for item in course_list: # item can be a course or a selective slot
                    if isinstance(item, dict):
                        # Augment with department title (for display in tables)
                        dept_id = item.get('department_id')
                        if dept_id is not None:
                            try:
                                item['department_title'] = department_map.get(int(dept_id))
                            except (ValueError, TypeError):
                                item['department_title'] = None
                        
                        # Sum hours for overall totals
                        hours_data = item.get('hours', {})
                        if isinstance(hours_data, dict):
                            overall_totals['lecture'] += int(hours_data.get('lecture', 0) or 0)
                            overall_totals['practice'] += int(hours_data.get('practice', 0) or 0)
                            overall_totals['laboratory'] += int(hours_data.get('laboratory', 0) or 0)
                            overall_totals['seminar'] += int(hours_data.get('seminar', 0) or 0)
            
        context['overall_hour_totals'] = overall_totals
        return context

@require_POST
@csrf_protect
def update_course_data_view(request, pk):
    try:
        curriculum = get_object_or_404(Curriculum, pk=pk)
        data = json.loads(request.body)
        
        item_identifier = data.get('course_code')
        field_name = data.get('field_name')
        new_value_str = data.get('new_value')

        if not item_identifier or not field_name:
            return JsonResponse({'status': 'error', 'message': 'Missing item_identifier or field_name in request.'}, status=400)

        # Allow new_value_str to be None only if field_name is 'department_id' (for clearing)
        if new_value_str is None and field_name != 'department_id':
            return JsonResponse({'status': 'error', 'message': f'Missing new_value for field {field_name}.'}, status=400)
        
        # If new_value_str is None and it's for department_id, treat as empty string for downstream logic before conversion
        if new_value_str is None and field_name == 'department_id':
            new_value_str = ''

        if not curriculum.data or not isinstance(curriculum.data, dict):
            curriculum.data = {"mandatory_courses": [], "selective_courses": []}

        mandatory_courses = curriculum.data.get('mandatory_courses', [])
        selective_course_slots = curriculum.data.get('selective_courses', [])
        
        item_found = False
        item_to_update = None

        for course_item_candidate in mandatory_courses:
            if isinstance(course_item_candidate, dict) and course_item_candidate.get('course_code') == item_identifier:
                item_to_update = course_item_candidate
                item_found = True
                break
        
        if not item_found and item_identifier and item_identifier.startswith('selective_slot_'):
            try:
                slot_number_str = item_identifier.replace('selective_slot_', '')
                target_slot_number = int(slot_number_str)
                for slot_item_candidate in selective_course_slots:
                    if isinstance(slot_item_candidate, dict) and slot_item_candidate.get('slot_number') == target_slot_number:
                        item_to_update = slot_item_candidate
                        item_found = True
                        break
            except ValueError: 
                pass 

        if not item_found or item_to_update is None: 
            return JsonResponse({'status': 'error', 'message': 'Course or slot not found.'}, status=404)

        keys = field_name.split('.')
        temp_target = item_to_update 
        
        for i, key_part in enumerate(keys[:-1]):
            if key_part not in temp_target or not isinstance(temp_target[key_part], dict):
                if key_part in ['hours', 'credits']:
                    temp_target[key_part] = {}
                else:
                    return JsonResponse({'status': 'error', 'message': f'Invalid field path component: {key_part} in {field_name}'}, status=400)
            temp_target = temp_target[key_part]
        
        original_field_value_at_key = temp_target.get(keys[-1])
        
        new_value = new_value_str 
        
        # Corrected is_numeric_field check for clarity and to avoid syntax error
        last_key = keys[-1]
        is_numeric_field = (last_key in ['total_hours', 'lecture', 'practice', 'laboratory', 'seminar', 'independent', 'total_credits']) or \
                           (len(keys) > 1 and keys[0] == 'credits' and last_key.isdigit())
        
        is_hour_component = field_name.startswith('hours.') and last_key in ['lecture', 'practice', 'laboratory', 'seminar', 'independent']

        if field_name == 'department_id':
            if not new_value_str.strip(): # Empty string or spaces only
                new_value = None  # Intend to remove/clear the department_id
            else:
                try:
                    new_value = int(new_value_str)
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid department ID format. Must be an integer or empty.'}, status=400)
        elif is_numeric_field:
            try:
                if new_value_str.strip() == '' or new_value_str.strip() == '-':
                    new_value = 0 
                else:
                    new_value = int(new_value_str)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': f'Invalid number format for {field_name}. Expected integer.'}, status=400)
        elif field_name == 'course_title': 
            new_value = str(new_value_str) # Ensure it's a string
        # else: new_value remains new_value_str (e.g. for other potential string fields)

        # Assign the new value or remove the key if new_value is None (specifically for department_id)
        if new_value is None and field_name == 'department_id':
            if last_key in temp_target:
                del temp_target[last_key]
        else:
            temp_target[last_key] = new_value
        
        if is_hour_component and new_value != original_field_value_at_key: # Check for actual change
            hours_data = item_to_update.get('hours', {})
            new_total_hours = (
                int(hours_data.get('lecture', 0) or 0) + 
                int(hours_data.get('practice', 0) or 0) + 
                int(hours_data.get('laboratory', 0) or 0) + 
                int(hours_data.get('seminar', 0) or 0) + 
                int(hours_data.get('independent', 0) or 0)
            )
            item_to_update['total_hours'] = new_total_hours
        
        curriculum.save()
        return JsonResponse({'status': 'success', 'message': 'Data updated successfully.', 'updated_item': item_to_update})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON in request.'}, status=400)
    except Exception as e:
        # Log the exception e for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
