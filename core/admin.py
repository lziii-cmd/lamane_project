from django.contrib import admin

# Register your models here.
# core/admin.py
# Charge tous les ModelAdmin définis dans core/admins/
from .admins import *  # noqa: F401,F403
