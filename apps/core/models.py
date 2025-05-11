from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model."""
    
    use_in_migrations = True
    
    def _create_user(self, username, email, password, **extra_fields):
        """Create and save a User with the given username, email and password."""
        if not username:
            raise ValueError('The given username must be set')
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a regular User with the given username, email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email, password, **extra_fields):
        """Create and save a SuperUser with the given username, email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model that supports three different user types"""
    
    # User types
    ACADEMIC_ADMIN = 'academic_admin'
    DEPARTMENT_HEAD = 'department_head'
    PROFESSOR = 'professor'
    
    USER_TYPE_CHOICES = [
        (ACADEMIC_ADMIN, _('Academic Affairs Office Admin')),
        (DEPARTMENT_HEAD, _('Department Head')),
        (PROFESSOR, _('Professor')),
    ]
    
    # Keep username field which comes from AbstractUser
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=PROFESSOR,
    )
    department = models.ForeignKey(
        'departments.Department', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='staff_members', # or 'users' or 'professors_in_department'
        help_text=_("The department this user belongs to, if applicable.")
    )
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    
    # Keep username as the default field for login
    USERNAME_FIELD = 'username'
    # Email is still required
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.username}: {self.first_name} {self.last_name} ({self.get_user_type_display()})"
    
    def is_academic_admin(self):
        return self.user_type == self.ACADEMIC_ADMIN
    
    def is_department_head(self):
        return self.user_type == self.DEPARTMENT_HEAD
    
    def is_professor(self):
        return self.user_type == self.PROFESSOR
