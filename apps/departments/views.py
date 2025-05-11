from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView
from django.contrib import messages
from .models import Department
from .forms import DepartmentForm
from apps.core.models import User # Make sure User is imported
from apps.professors.models import Professor # Import the Professor model

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
        return context
