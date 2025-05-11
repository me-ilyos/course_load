from django import forms
from django.db.models import Q # Import Q
from .models import Department
from apps.core.models import User # Import User model

class DepartmentForm(forms.ModelForm):
    # Define department_head field explicitly to customize queryset
    department_head = forms.ModelChoiceField(
        queryset=User.objects.filter(
            Q(user_type=User.PROFESSOR) | Q(user_type=User.DEPARTMENT_HEAD)
        ).order_by('last_name', 'first_name'),
        required=False, # A department might not have a head initially
        label="Kafedra Mudiri",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Kafedra mudirini tanlang. Agar tayinlanmagan bo'lsa, bo'sh qoldiring."
    )

    class Meta:
        model = Department
        fields = ['title', 'code', 'department_head'] # Added 'department_head'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            # 'department_head' widget is defined above for customization
        } 