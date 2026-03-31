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
        "deletion_reason_preview",
        "created_at",
    )
    list_filter = ("priority", "due_date", "completado", "deleted_at")
    search_fields = ("title", "description", "deletion_reason", "user__email")
    raw_id_fields = ("user",)
    date_hierarchy = "due_date"
    readonly_fields = ("deletion_reason",)

    @admin.display(description="Motivo borrado")
    def deletion_reason_preview(self, obj):
        if not obj.deletion_reason:
            return "—"
        text = obj.deletion_reason.strip()
        if len(text) > 60:
            return text[:60] + "…"
        return text

    def get_queryset(self, request):
        return Task.all_tasks.select_related("user")
