from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.contrib import messages
from .models import Department
from .forms import DepartmentForm
from apps.core.models import User # Make sure User is imported
from apps.professors.models import Professor # Import the Professor model
from apps.curricula.models import Curriculum # Import Curriculum model
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

# Create your views here.

class DepartmentListView(ListView):
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DepartmentForm()
        return context

class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    success_url = reverse_lazy('departments:department_list') # Redirect to the list view on success

    def form_valid(self, form):
        messages.success(self.request, "Kafedra muvaffaqiyatli qo'shildi.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Prepare error messages for each field
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"<strong>{form.fields[field].label}:</strong> {error}")
        
        # Join all error messages into a single HTML string
        if error_messages:
            messages.error(self.request, f"Kafedrani qo'shishda xatolik yuz berdi:<br>{'<br>'.join(error_messages)}")
        else:
            messages.error(self.request, "Kafedrani qo'shishda noma'lum xatolik yuz berdi. Iltimos, maydonlarni tekshiring.")
        
        # To display the form again with errors, we need to render the list view's template
        # with the invalid form and existing departments.
        # This is a bit tricky with CreateView directly. A common pattern is to handle POST
        # in the ListView or use a separate function view.
        # For simplicity here, we'll redirect back to the list view, and the errors will be displayed
        # via Django messages. The modal won't automatically reopen with errors,
        # but the user will see the errors.
        # A more sophisticated solution would involve AJAX or more complex view logic.
        return redirect(reverse_lazy('departments:department_list'))

class DepartmentDetailView(DetailView):
    model = Department
    template_name = 'departments/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department_obj = self.object
        
        # Get Professor profiles linked to this department, ensuring user data is also fetched efficiently
        professor_profiles = Professor.objects.filter(department=department_obj).select_related('user')
        
        context['professor_profiles'] = professor_profiles # Pass Professor objects
        # The old 'professors' context variable (which was a list of User objects) is no longer needed.

        # --- Fetch assigned courses --- 
        assigned_courses_data = []
        all_curricula = Curriculum.objects.filter(data__isnull=False)

        for curriculum in all_curricula:
            if not isinstance(curriculum.data, dict):
                continue

            mandatory = curriculum.data.get('mandatory_courses', [])
            selective = curriculum.data.get('selective_courses', [])
            
            for course_list, course_type in [(mandatory, 'Mandatory'), (selective, 'Selective Slot')]:
                for item in course_list:
                    # Check if the item is a dict and assigned to the current department
                    if isinstance(item, dict) and item.get('department_id') == department_obj.id:
                        course_info = {
                            'curriculum_title': curriculum.title,
                            'curriculum_code': curriculum.code,
                            'curriculum_year': curriculum.academic_year_display,
                            'course_type': course_type,
                            'course_code': item.get('course_code', 'N/A') if course_type == 'Mandatory' else f"Slot {item.get('slot_number', '?')}",
                            'course_title': item.get('course_title', 'N/A') if course_type == 'Mandatory' else f"Selective Slot {item.get('slot_number', '?')}", # Or display options?
                            'hours': item.get('hours', {}),
                            # Add other relevant details if needed
                        }
                        assigned_courses_data.append(course_info)
        
        context['assigned_courses'] = assigned_courses_data
        # --- End Fetch assigned courses --- 
        
        return context

# Function-based views for AJAX handling of create/update/delete

def department_create_view(request):
    # Check if the request is AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            if is_ajax:
                # For AJAX, return success status
                return JsonResponse({'status': 'success', 'message': 'Department created successfully.'})
            else:
                # For non-AJAX, redirect like the CBV
                messages.success(request, "Kafedra muvaffaqiyatli qo'shildi.")
                return redirect(reverse_lazy('departments:department_list'))
        else:
            if is_ajax:
                # For AJAX, return errors
                errors = form.errors.as_json()
                return JsonResponse({'status': 'error', 'message': 'Form validation failed', 'errors': errors}, status=400)
            else:
                # For non-AJAX, mimic CBV invalid logic (show messages, redirect)
                error_messages = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        error_messages.append(f"<strong>{form.fields[field].label}:</strong> {error}")
                if error_messages:
                    messages.error(request, f"Kafedrani qo'shishda xatolik yuz berdi:<br>{'<br>'.join(error_messages)}")
                else:
                    messages.error(request, "Kafedrani qo'shishda noma'lum xatolik yuz berdi. Iltimos, maydonlarni tekshiring.")
                return redirect(reverse_lazy('departments:department_list')) # Redirect back
    else:
        # Handle GET requests (e.g., if accessed directly, though unlikely for this pattern)
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'GET request not supported for creation via AJAX.'}, status=405)
        else:
            # Redirect to list if accessed via GET non-AJAX
            return redirect(reverse_lazy('departments:department_list'))

# TODO: Implement similar function-based views for update and delete if needed for AJAX

