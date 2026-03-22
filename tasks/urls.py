from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.TaskBoardView.as_view(), name="board"),
    path("partial/", views.TaskBoardPartialView.as_view(), name="board_partial"),
    path("create/", views.TaskCreateView.as_view(), name="task_create"),
    path("weekly-report/", views.WeeklyReportPartialView.as_view(), name="weekly_report"),
    path("<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path(
        "<int:pk>/toggle-complete/",
        views.TaskToggleCompleteView.as_view(),
        name="task_toggle_complete",
    ),
]
