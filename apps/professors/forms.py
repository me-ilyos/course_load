from django import forms
from django.contrib.auth.hashers import make_password
from apps.core.models import User
from apps.departments.models import Department
from .models import Professor
import uuid # Import uuid for ID generation

class ProfessorForm(forms.ModelForm):
    # User fields
    username = forms.CharField(max_length=150, required=True, label="Foydalanuvchi nomi (login)")
    email = forms.EmailField(required=True, label="Elektron pochta")
    first_name = forms.CharField(max_length=150, required=True, label="Ismi")
    last_name = forms.CharField(max_length=150, required=True, label="Familiyasi")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Parol")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Parolni tasdiqlang")
    
    user_type = forms.ChoiceField(
        choices=[
            (User.PROFESSOR, "Professor"),
            (User.DEPARTMENT_HEAD, "Kafedra Mudiri"),
        ],
        required=True,
        label="Foydalanuvchi Turi"
    )
    department_user = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False, # Department for User model, can be optional here as Professor model also has it
        label="Kafedra (asosiy)",
        help_text="Foydalanuvchi umumiy bog'lanadigan kafedra (ixtiyoriy)."
    )

    # Professor fields (employee_id removed from here)
    # employee_id = forms.CharField(max_length=20, required=True, label="Xodim ID raqami") # Removed
    title = forms.CharField(max_length=50, required=True, label="Lavozimi (masalan, dotsent, professor)")
    employment_type = forms.ChoiceField(choices=Professor.EMPLOYMENT_CHOICES, required=True, label="Stavka")
    is_degree_holder = forms.BooleanField(required=False, label="Ilmiy darajasi bor (PhD yoki DSc)")
    department_professor = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True, # Department for Professor profile, usually required
        label="Kafedra (professor profili uchun)"
    )

    class Meta:
        model = Professor
        # fields = ['employee_id', 'title', 'employment_type', 'is_degree_holder'] # employee_id removed
        fields = ['title', 'employment_type', 'is_degree_holder'] # Updated fields

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and hasattr(self.instance, 'user'):
            user_instance = self.instance.user
            self.fields['username'].initial = user_instance.username
            self.fields['email'].initial = user_instance.email
            self.fields['first_name'].initial = user_instance.first_name
            self.fields['last_name'].initial = user_instance.last_name
            self.fields['user_type'].initial = user_instance.user_type
            self.fields['department_user'].initial = user_instance.department
            
            # For updates, password fields are not pre-filled and not required unless changed
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            
            # Professor model fields
            self.fields['department_professor'].initial = self.instance.department


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.instance and self.instance.pk and hasattr(self.instance, 'user'): # Editing existing
            if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError("Bu foydalanuvchi nomi allaqachon mavjud.")
        elif User.objects.filter(username=username).exists(): # Creating new
            raise forms.ValidationError("Bu foydalanuvchi nomi allaqachon mavjud.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.pk and hasattr(self.instance, 'user'): # Editing existing
            if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError("Bu elektron pochta allaqachon ishlatilgan.")
        elif User.objects.filter(email=email).exists(): # Creating new
             raise forms.ValidationError("Bu elektron pochta allaqachon ishlatilgan.")
        return email

    # Removed clean_employee_id as the field is removed
    # def clean_employee_id(self):
    #     employee_id = self.cleaned_data.get('employee_id')
    #     query = Professor.objects.filter(employee_id=employee_id)
    #     if self.instance and self.instance.pk: # Editing
    #         query = query.exclude(pk=self.instance.pk)
    #     if query.exists():
    #         raise forms.ValidationError("Bu xodim ID raqami allaqachon mavjud.")
    #     return employee_id

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Password validation only if password is being set/changed
        if self.instance and self.instance.pk: # Editing
            if password and password != confirm_password:
                self.add_error('confirm_password', "Parollar bir xil emas.")
        else: # Creating
            if not password:
                 self.add_error('password', "Parol kiritilishi shart.")
            elif password != confirm_password:
                self.add_error('confirm_password', "Parollar bir xil emas.")
        return cleaned_data

    def save(self, commit=True):
        # --- User Creation/Update (same as before) ---
        user_data = {
            'username': self.cleaned_data['username'],
            'email': self.cleaned_data['email'],
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'user_type': self.cleaned_data['user_type'],
            'department': self.cleaned_data.get('department_user') 
        }
        
        is_new_user = not (self.instance and self.instance.pk and hasattr(self.instance, 'user'))

        if not is_new_user: # Update existing user
            user = self.instance.user
            # Update fields
            user.username = user_data['username']
            user.email = user_data['email']
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.user_type = user_data['user_type']
            user.department = user_data['department']
            if self.cleaned_data.get('password'): # Update password if provided
                user.password = make_password(self.cleaned_data['password'])
        else: # Create new user
            user_data['password'] = make_password(self.cleaned_data['password'])
            user = User.objects.create_user(**user_data)

        if commit:
            user.save()

        # --- Professor Creation/Update ---
        professor = super().save(commit=False)
        professor.user = user
        professor.department = self.cleaned_data['department_professor']
        
        # --- Generate employee_id if creating new professor ---
        if is_new_user or not professor.employee_id:
            # Generate a unique ID (e.g., using UUID) - ensure it fits max_length=20
            new_id = uuid.uuid4().hex[:10].upper() # Example: 10 hex chars
            # Optional: Add prefix/logic based on department/year etc. if needed
            # Ensure uniqueness (though UUID collision is highly unlikely)
            while Professor.objects.filter(employee_id=new_id).exists():
                new_id = uuid.uuid4().hex[:10].upper()
            professor.employee_id = new_id
        
        if commit:
            professor.save()
            
        return professor 