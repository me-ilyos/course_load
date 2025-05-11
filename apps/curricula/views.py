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
from .parser import extract_mandatory_courses
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
                    
                    parsed_data = extract_mandatory_courses(temp_excel_path)
                    curriculum_instance.data = parsed_data
                    
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
        
        course_code = data.get('course_code')
        field_name = data.get('field_name')
        new_value_str = data.get('new_value')

        if not all([course_code, field_name, new_value_str is not None]):
            return JsonResponse({'status': 'error', 'message': 'Missing data in request.'}, status=400)

        if not curriculum.data or not isinstance(curriculum.data, list):
            curriculum.data = []

        course_found = False
        for course_item in curriculum.data:
            if isinstance(course_item, dict) and course_item.get('course_code') == course_code:
                keys = field_name.split('.')
                target_dict = course_item
                original_field_value = None # To check if relevant hour field changed

                # Navigate to the target dictionary for update
                temp_target = course_item
                for i, key_part in enumerate(keys[:-1]):
                    if key_part not in temp_target or not isinstance(temp_target[key_part], dict):
                        return JsonResponse({'status': 'error', 'message': f'Invalid field path for assignment: {field_name}'}, status=400)
                    temp_target = temp_target[key_part]
                original_field_value = temp_target.get(keys[-1])
                
                # Determine the correct type for the new_value
                new_value = new_value_str 
                is_numeric_field = keys[-1] in ['total_hours', 'lecture', 'practice', 'laboratory', 'seminar', 'independent', 'total_credits'] or keys[0] == 'credits'
                is_hour_component = field_name.startswith('hours.')

                if is_numeric_field:
                    try:
                        if new_value_str.strip() == '' or new_value_str.strip() == '-':
                            new_value = 0 
                        else:
                            new_value = int(new_value_str)
                    except ValueError:
                        return JsonResponse({'status': 'error', 'message': f'Invalid number format for {field_name}.'}, status=400)
                elif field_name == 'course_title':
                    new_value = str(new_value_str)
                # Add other type conversions if necessary

                # Assign the new value
                temp_target[keys[-1]] = new_value
                course_found = True

                # If an hour component was updated, recalculate total_hours (Hajmi)
                if is_hour_component and new_value != original_field_value: # Check if value actually changed
                    hours_data = course_item.get('hours', {})
                    new_total_hours = (
                        hours_data.get('lecture', 0) + 
                        hours_data.get('practice', 0) + 
                        hours_data.get('laboratory', 0) + 
                        hours_data.get('seminar', 0) + 
                        hours_data.get('independent', 0)
                    )
                    course_item['total_hours'] = new_total_hours
                break        
        
        if not course_found:
            return JsonResponse({'status': 'error', 'message': 'Course code not found.'}, status=404)

        curriculum.save()
        return JsonResponse({'status': 'success', 'message': 'Course data updated.'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON in request.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)
