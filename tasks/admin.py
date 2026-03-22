from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "due_date",
        "priority",
        "completado",
        "deleted_at",
        "created_at",
    )
    list_filter = ("priority", "due_date", "completado", "deleted_at")
    search_fields = ("title", "description", "user__email")
    raw_id_fields = ("user",)
    date_hierarchy = "due_date"

    def get_queryset(self, request):
        return Task.all_tasks.select_related("user")
