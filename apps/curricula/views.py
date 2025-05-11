import re
from django.shortcuts import render, redirect, get_object_or_404
import openpyxl
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from .models import Curriculum
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
    # Note: For DetailView, typically you would use DetailView as base class
    # and it uses a slug or pk from URL to fetch a single object.
    # If this is intended to be a DetailView, it should inherit from django.views.generic.DetailView

@require_POST
@csrf_protect
def update_course_data_view(request, pk):
    try:
        curriculum = get_object_or_404(Curriculum, pk=pk)
        data = json.loads(request.body)
        
        item_identifier = data.get('course_code') # This can be actual course_code or "selective_slot_{slot_num}"
        field_name = data.get('field_name')
        new_value_str = data.get('new_value')

        if not all([item_identifier, field_name, new_value_str is not None]):
            return JsonResponse({'status': 'error', 'message': 'Missing data in request.'}, status=400)

        if not curriculum.data or not isinstance(curriculum.data, dict):
            curriculum.data = {"mandatory_courses": [], "selective_courses": []} # Ensure basic structure

        mandatory_courses = curriculum.data.get('mandatory_courses', [])
        selective_course_slots = curriculum.data.get('selective_courses', [])
        
        item_found = False
        item_to_update = None
        # No specific item_type needed here for now, logic handles course_item or slot_item directly

        # Try to find in mandatory courses
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
                        item_to_update = slot_item_candidate # The slot itself is updated
                        item_found = True
                        break
            except ValueError: # if slot_number_str is not an int
                pass # item_found remains False

        if not item_found or item_to_update is None: # Check item_to_update is not None
            return JsonResponse({'status': 'error', 'message': 'Course or slot not found.'}, status=404)

        # Proceed with updating item_to_update (which is either a course dict or a slot dict)
        keys = field_name.split('.')
        target_dict_for_update = item_to_update # Renamed for clarity
        original_field_value = None

        # Navigate to the target dictionary for update
        temp_target = target_dict_for_update
        for i, key_part in enumerate(keys[:-1]):
            if key_part not in temp_target or not isinstance(temp_target[key_part], dict):
                # If path doesn't exist for 'hours' or 'credits', create it.
                if key_part in ['hours', 'credits'] and (key_part not in temp_target or not isinstance(temp_target.get(key_part), dict)):
                    temp_target[key_part] = {}
                elif key_part.isdigit() and keys[i-1] == 'credits' and (key_part not in temp_target or not isinstance(temp_target.get(key_part), (int,str,float))): # for credits.1, credits.2 etc.
                     pass # Will be set directly
                else:
                    return JsonResponse({'status': 'error', 'message': f'Invalid field path for assignment: {field_name}'}, status=400)
            temp_target = temp_target[key_part]
        
        original_field_value_at_key = temp_target.get(keys[-1])
        
        # Determine the correct type for the new_value
        new_value = new_value_str
        # Adjusted numeric field check to be more general or specific to known fields
        is_numeric_field = keys[-1] in ['total_hours', 'lecture', 'practice', 'laboratory', 'seminar', 'independent', 'total_credits'] or \
                           (keys[0] == 'credits' and keys[-1].isdigit()) # e.g. credits.1, credits.2
        
        is_hour_component = field_name.startswith('hours.') and keys[-1] in ['lecture', 'practice', 'laboratory', 'seminar', 'independent']

        if is_numeric_field:
            try:
                if new_value_str.strip() == '' or new_value_str.strip() == '-':
                    new_value = 0 
                else:
                    new_value = int(new_value_str)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': f'Invalid number format for {field_name}.'}, status=400)
        elif field_name == 'course_title': # course_title is only for mandatory courses
            new_value = str(new_value_str)
        # Add other type conversions if necessary for other fields

        # Assign the new value
        temp_target[keys[-1]] = new_value
        
        # If an hour component was updated, recalculate total_hours for the item_to_update
        if is_hour_component and new_value != original_field_value_at_key:
            hours_data = target_dict_for_update.get('hours', {})
            new_total_hours = (
                int(hours_data.get('lecture', 0) or 0) + 
                int(hours_data.get('practice', 0) or 0) + 
                int(hours_data.get('laboratory', 0) or 0) + 
                int(hours_data.get('seminar', 0) or 0) + 
                int(hours_data.get('independent', 0) or 0)
            )
            target_dict_for_update['total_hours'] = new_total_hours
        # No break needed here as we've already found and are processing item_to_update
        
        curriculum.save()
        return JsonResponse({'status': 'success', 'message': 'Data updated successfully.'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON in request.'}, status=400)
    except Exception as e:
        # Log the exception e for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
