from datetime import date, timedelta

from django.db.models import Count, Q

from .models import Task


def iso_week_bounds(iso_year: int, iso_week: int) -> tuple[date, date]:
    start = date.fromisocalendar(iso_year, iso_week, 1)
    end = date.fromisocalendar(iso_year, iso_week, 7)
    return start, end


def adjacent_iso_weeks(iso_year: int, iso_week: int) -> tuple[tuple[int, int], tuple[int, int]]:
    start, _ = iso_week_bounds(iso_year, iso_week)
    prev = start - timedelta(days=7)
    nxt = start + timedelta(days=7)
    pi = prev.isocalendar()
    ni = nxt.isocalendar()
    return (pi.year, pi.week), (ni.year, ni.week)


def weekly_task_stats(user, iso_year: int, iso_week: int) -> dict:
    """
    Tareas con fecha programada (`due_date`) en la semana ISO indicada (incluye
    soft-deleted en el total y en “eliminadas”), desglose activas vs eliminadas
    y porcentaje de completadas entre activas (completadas / (completadas + pendientes);
    las eliminadas no entran en el denominador).
    """
    start_d, end_d = iso_week_bounds(iso_year, iso_week)
    qs = Task.all_tasks.filter(
        user=user,
        due_date__gte=start_d,
        due_date__lte=end_d,
    )
    agg = qs.aggregate(
        total=Count("pk"),
        completadas=Count(
            "pk",
            filter=Q(completado=True, deleted_at__isnull=True),
        ),
        pendientes=Count(
            "pk",
            filter=Q(completado=False, deleted_at__isnull=True),
        ),
        eliminadas=Count(
            "pk",
            filter=Q(deleted_at__isnull=False),
        ),
    )
    total = agg["total"] or 0
    completadas = agg["completadas"] or 0
    pendientes = agg["pendientes"] or 0
    eliminadas = agg["eliminadas"] or 0
    activas = completadas + pendientes
    pct = round(100 * completadas / activas, 1) if activas else 0.0
    return {
        "week_start": start_d,
        "week_end": end_d,
        "iso_year": iso_year,
        "iso_week": iso_week,
        "total": total,
        "completadas": completadas,
        "pendientes": pendientes,
        "eliminadas": eliminadas,
        "porcentaje_completadas": pct,
    }
