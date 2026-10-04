from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ShortURL

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
        "short_code",
        "original_url",
        "clicks",
        "created_at"
    )
    search_fields = ("short_code", "original_url")
    list_filter = ("created_at",)