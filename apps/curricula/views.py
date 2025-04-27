import re
from django.shortcuts import render
import openpyxl
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .parsing import parse_curriculum_metadata

# Create your views here.

@csrf_exempt
def parse_curriculum_excel(request):
    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.worksheets[0]  # Always parse the first sheet
        data = parse_curriculum_metadata(ws)
        return HttpResponse(f"Parsed data: {data}")
    return render(request, 'curricula/upload_excel.html')
