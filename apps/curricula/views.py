import re
from django.shortcuts import render, redirect
import openpyxl
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .parsing import parse_curriculum_metadata
from django.views.generic import ListView
from .models import Curriculum
from .forms import CurriculumForm
from django.contrib import messages
from django.urls import reverse_lazy

# Create your views here.

@csrf_exempt
def parse_curriculum_excel(request):
    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        ws = wb.worksheets[0]  # Always parse the first sheet
        data = parse_curriculum_metadata(ws)
        return JsonResponse(data)
    return render(request, 'curricula/upload_excel.html')

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
        form = CurriculumForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "O'quv rejasi muvaffaqiyatli qo'shildi.")
            return redirect(reverse_lazy('curricula:curriculum_list'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
            return redirect(reverse_lazy('curricula:curriculum_list'))
    return redirect(reverse_lazy('curricula:curriculum_list'))


def upload_excel(request):
    return render(request, 'curricula/upload_excel.html')

# Example of a function-based view if preferred for simpler cases:
# def curriculum_list_view(request):
#     curricula = Curriculum.objects.all().order_by('title', 'start_year')
#     return render(request, 'curricula/curriculum_list.html', {'curricula': curricula})
