from django import forms
from django.core.exceptions import ValidationError

from .models import Task

MAX_DIAS_RANGO = 62


class TaskForm(forms.ModelForm):
    """Campos year/month/day conservan el mes y día seleccionados en el calendario (HTMX POST)."""

    year = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    month = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    day = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    due_date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha fin (opcional)",
        help_text="Si la rellenas, se crea la misma tarea en cada día del rango.",
    )

    class Meta:
        model = Task
        fields = ("title", "description", "due_date", "priority", "completado")
        labels = {
            "title": "Título",
            "description": "Descripción",
            "due_date": "Fecha",
            "priority": "Prioridad",
            "completado": "Completada",
        }
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "completado": forms.CheckboxInput(attrs={"class": "task-checkbox"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("due_date")
        end = cleaned.get("due_date_end")
        if start and end:
            if end < start:
                raise ValidationError(
                    {"due_date_end": "La fecha fin no puede ser anterior a la de inicio."}
                )
            dias = (end - start).days + 1
            if dias > MAX_DIAS_RANGO:
                raise ValidationError(
                    {
                        "due_date_end": f"El rango no puede superar {MAX_DIAS_RANGO} días."
                    }
                )
        return cleaned
