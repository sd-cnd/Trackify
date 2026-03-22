from django.contrib import admin
from .models import Holiday


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'date',
        'type',
        'region',
        'created_by'
    )

    list_filter = ('type', 'date', 'region')

    search_fields = ('name',)

    autocomplete_fields = ['created_by']