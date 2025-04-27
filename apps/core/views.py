from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect based on user type
            if user.is_academic_admin():
                return redirect('academic_admin_dashboard')
            elif user.is_department_head():
                return redirect('department_head_dashboard')
            else:  # Professor
                return redirect('professor_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def academic_admin_dashboard(request):
    if not request.user.is_academic_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')
    
    return render(request, 'core/academic_admin_dashboard.html')


@login_required
def department_head_dashboard(request):
    if not request.user.is_department_head():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')
    
    # In a real app, you'd fetch the department the user is head of
    # For now, we'll just pass a dummy context
    context = {
        'department': {'name': 'Sample Department'}
    }
    
    return render(request, 'core/department_head_dashboard.html', context)


@login_required
def professor_dashboard(request):
    if not request.user.is_professor() and not request.user.is_department_head():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')
    
    return render(request, 'core/professor_dashboard.html')
