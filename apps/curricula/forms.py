from django import forms
from .models import Curriculum

class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = ['code', 'title', 'start_year', 'degree', 'duration', 'data']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'start_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'degree': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'data': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter JSON data or leave blank'}),
        }
        labels = {
            'code': "Kod",
            'title': "Nomi",
            'start_year': "Boshlanish yili (YYYY)",
            'degree': "Darajasi",
            'duration': "Davomiyligi (yil)",
            'data': "Qo'shimcha ma'lumotlar (JSON)"
        }
        help_texts = {
            'data': "Majburiy va tanlov fanlari haqida JSON formatidagi ma\'lumotlar. Bo\'sh qoldirilishi mumkin."
        }

    def clean_start_year(self):
        start_year = self.cleaned_data.get('start_year')
        if start_year and (start_year < 1900 or start_year > 2100):
            raise forms.ValidationError("Iltimos, to'g'ri yil kiriting (1900-2100).")
        return start_year

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        degree = self.cleaned_data.get('degree')
        if duration:
            if degree == 'Bachelors' and duration != 4:
                raise forms.ValidationError("Bakalavr uchun davomiylik 4 yil bo'lishi kerak.")
            elif degree == 'Masters' and duration != 2:
                raise forms.ValidationError("Magistratura uchun davomiylik 2 yil bo'lishi kerak.")
        return duration 