from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models.user_model import User

# Register your models here.
admin.site.register(User, UserAdmin)
