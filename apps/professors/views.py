from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Professor
from apps.core.models import User
from .forms import ProfessorForm
from django.db.models import Q

class ProfessorListView(LoginRequiredMixin, ListView):
    model = Professor
    template_name = 'professors/professor_list.html'
    context_object_name = 'professors'
    paginate_by = 10

    def get_queryset(self):
        queryset = Professor.objects.select_related('user', 'department').order_by('user__last_name', 'user__first_name')
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(department__title__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = ProfessorForm()
        context['user_types'] = User.USER_TYPE_CHOICES
        context['search_query'] = self.request.GET.get('q', '')
        return context

    def post(self, request, *args, **kwargs):
        form = ProfessorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Professor muvaffaqiyatli qo'shildi.")
            return redirect(reverse_lazy('professors:professor_list'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields[field].label if field in form.fields else field.replace('_', ' ').title()
                    messages.error(request, f"{field_name}: {error}")
            self.object_list = self.get_queryset()
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

class ProfessorUpdateView(LoginRequiredMixin, UpdateView):
    model = Professor
    form_class = ProfessorForm
    template_name = 'professors/professor_form.html'
    success_url = reverse_lazy('professors:professor_list')

    def form_valid(self, form):
        messages.success(self.request, "Professor ma'lumotlari muvaffaqiyatli yangilandi.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                field_name = form.fields[field].label if field in form.fields else field.replace('_', ' ').title()
                messages.error(self.request, f"{field_name}: {error}")
        return self.render_to_response(self.get_context_data(form=form))


class ProfessorDeleteView(LoginRequiredMixin, DeleteView):
    model = Professor
    template_name = 'professors/professor_confirm_delete.html'
    success_url = reverse_lazy('professors:professor_list')

    def form_valid(self, form):
        messages.success(self.request, f"Professor '{self.object.user.get_full_name()}' muvaffaqiyatli o'chirildi.")
        return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Professorni o'chirish: {self.object.user.get_full_name()}"
        return context
