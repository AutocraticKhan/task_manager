"""
URL configuration for test_task_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from task_manager import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("all_tasks/", views.all_tasks, name="all_tasks"),
    path("today_tasks/", views.today_tasks, name="today_tasks"),
    path("completed_tasks/", views.completed_tasks, name="completed_tasks"),
    path("add_task/", views.add_task, name="add_task"),
    path("task_breakdown/", views.task_breakdown, name="task_breakdown"),
    path("redistribute_tasks/", views.redistribute_tasks_view, name="redistribute_tasks"),
    path('complete_subtask/<int:subtask_id>/', views.complete_subtask, name='complete_subtask'),
    path('task_detail/<int:task_id>/', views.task_detail, name='task_detail'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
]
