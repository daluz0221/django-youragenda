import calendar
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from .forms import TaskForm
from .models import Task
from .services import adjacent_iso_weeks, weekly_task_stats


def _clamp_month(y: int, m: int) -> tuple[int, int]:
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


def _parse_board_params(request) -> tuple[date, int, int]:
    today = timezone.localdate()
    data = (
        request.POST
        if request.method == "POST" and request.POST.get("year") is not None
        else request.GET
    )
    y = int(data.get("year", today.year))
    m = int(data.get("month", today.month))
    y, m = _clamp_month(y, m)
    m = max(1, min(12, m))
    last = calendar.monthrange(y, m)[1]

    raw_day = data.get("day")
    if raw_day is not None and raw_day != "":
        d = max(1, min(last, int(raw_day)))
    elif today.year == y and today.month == m:
        d = min(today.day, last)
    else:
        d = 1

    return date(y, m, d), y, m


def _tasks_for_month(user, y: int, m: int):
    return (
        Task.objects.filter(user=user, due_date__year=y, due_date__month=m)
        .annotate(
            prio_order=Case(
                When(priority=Task.Priority.ALTA, then=0),
                When(priority=Task.Priority.MEDIA, then=1),
                When(priority=Task.Priority.BAJA, then=2),
                default=3,
                output_field=IntegerField(),
            )
        )
        .order_by("due_date", "prio_order", "pk")
    )


def _days_with_tasks_iso(tasks_qs):
    return {
        d.isoformat()
        for d in tasks_qs.values_list("due_date", flat=True).distinct()
    }


def build_board_context(request, task_form=None):
    selected, y, m = _parse_board_params(request)
    user = request.user
    month_tasks = _tasks_for_month(user, y, m)
    day_tasks = month_tasks.filter(due_date=selected).order_by(
        "completado", "prio_order", "pk"
    )
    days_with_tasks = _days_with_tasks_iso(month_tasks)

    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(y, m)

    prev_y, prev_m = y, m - 1
    if prev_m < 1:
        prev_m = 12
        prev_y -= 1
    next_y, next_m = y, m + 1
    if next_m > 12:
        next_m = 1
        next_y += 1

    if task_form is None:
        task_form = TaskForm(
            initial={
                "due_date": selected,
                "priority": Task.Priority.MEDIA,
                "year": y,
                "month": m,
                "day": selected.day,
            }
        )

    return {
        "selected_date": selected,
        "year": y,
        "month": m,
        "weeks": weeks,
        "day_tasks": day_tasks,
        "month_task_count": month_tasks.count(),
        "days_with_tasks": days_with_tasks,
        "prev_year": prev_y,
        "prev_month": prev_m,
        "next_year": next_y,
        "next_month": next_m,
        "task_form": task_form,
    }


class TaskBoardView(LoginRequiredMixin, TemplateView):
    template_name = "tasks/board.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_board_context(self.request))
        return ctx


class TaskBoardPartialView(LoginRequiredMixin, TemplateView):
    template_name = "tasks/partials/board_inner.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_board_context(self.request))
        return ctx


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm

    def get(self, request, *args, **kwargs):
        return redirect(reverse_lazy("tasks:board"))

    def form_valid(self, form):
        user = self.request.user
        cd = form.cleaned_data
        start = cd["due_date"]
        end = cd.get("due_date_end") or start
        title = cd["title"]
        description = cd["description"]
        priority = cd["priority"]

        tasks = []
        d = start
        while d <= end:
            tasks.append(
                Task(
                    user=user,
                    title=title,
                    description=description,
                    due_date=d,
                    priority=priority,
                    completado=False,
                    deleted_at=None,
                )
            )
            d += timedelta(days=1)

        Task.objects.bulk_create(tasks)
        self.object = tasks[0] if tasks else None

        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "tasks/partials/board_inner.html",
                build_board_context(self.request),
            )
        return redirect(reverse_lazy("tasks:board"))

    def form_invalid(self, form):
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "tasks/partials/board_inner.html",
                build_board_context(self.request, task_form=form),
                status=422,
            )
        return redirect(reverse_lazy("tasks:board"))


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    context_object_name = "task"

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        selected, y, m = _parse_board_params(self.request)
        init = kwargs.setdefault("initial", {})
        init.setdefault("year", y)
        init.setdefault("month", m)
        init.setdefault("day", selected.day)
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected, y, m = _parse_board_params(self.request)
        ctx["board_year"] = y
        ctx["board_month"] = m
        ctx["board_day"] = selected.day
        return ctx

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true" and self.request.method == "GET":
            return ["tasks/partials/task_edit_form.html"]
        return ["tasks/task_form_page.html"]

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "tasks/partials/board_inner.html",
                build_board_context(self.request),
            )
        return redirect(reverse_lazy("tasks:board"))

    def form_invalid(self, form):
        if self.request.headers.get("HX-Request") == "true":
            self.object = self.get_object()
            selected, y, m = _parse_board_params(self.request)
            return render(
                self.request,
                "tasks/partials/task_edit_form.html",
                {
                    "task": self.object,
                    "form": form,
                    "board_year": y,
                    "board_month": m,
                    "board_day": selected.day,
                },
                status=422,
            )
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("tasks:board")


class TaskDeleteView(LoginRequiredMixin, View):
    def delete(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        reason = request.POST.get("deletion_reason", "").strip()
        task.deleted_at = timezone.now()
        task.deletion_reason = reason
        task.save(update_fields=["deleted_at", "deletion_reason", "updated_at"])
        if request.headers.get("HX-Request") == "true":
            return render(
                request,
                "tasks/partials/board_inner.html",
                build_board_context(request),
            )
        return HttpResponse(status=204)

    def post(self, request, pk):
        return self.delete(request, pk)


class TaskToggleCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.completado = not task.completado
        task.save(update_fields=["completado", "updated_at"])
        if request.headers.get("HX-Request") == "true":
            return render(
                request,
                "tasks/partials/board_inner.html",
                build_board_context(request),
            )
        return redirect(reverse_lazy("tasks:board"))


class WeeklyReportPartialView(LoginRequiredMixin, TemplateView):
    template_name = "tasks/partials/weekly_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        iso = today.isocalendar()
        y = int(self.request.GET.get("year", iso.year))
        w = int(self.request.GET.get("week", iso.week))
        try:
            stats = weekly_task_stats(self.request.user, y, w)
            (py, pw), (ny, nw) = adjacent_iso_weeks(y, w)
        except ValueError:
            stats = weekly_task_stats(self.request.user, iso.year, iso.week)
            (py, pw), (ny, nw) = adjacent_iso_weeks(iso.year, iso.week)
        ctx.update(stats)
        ctx["prev_year"] = py
        ctx["prev_week"] = pw
        ctx["next_year"] = ny
        ctx["next_week"] = nw
        return ctx

