from django.shortcuts import render, redirect
from django.http import HttpResponse
from . import task_utils
from . import task_scheduler
from .models import Task, Subtask
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import LoginForm, SignupForm
from datetime import date, timedelta, datetime
import os

def home(request):
    return render(request, 'home.html')

@login_required
def all_tasks(request):
    tasks = Task.objects.filter(user=request.user)
    for task in tasks:
        task.subtasks = Subtask.objects.filter(task=task)
        total_subtasks = task.subtasks.count()
        completed_subtasks = task.subtasks.filter(completed=True).count()
        if total_subtasks > 0:
            task.completion_percentage = (completed_subtasks / total_subtasks) * 100
        else:
            task.completion_percentage = 0
    return render(request, 'all_tasks.html', {'tasks': tasks})

@login_required
def today_tasks(request):
    today = date.today()
    tasks = Task.objects.filter(user=request.user)
    today_tasks_list = []
    for task in tasks:
        # Get today's subtasks
        subtasks = Subtask.objects.filter(task=task, due_date=today, completed=False)
        
        # Get pending subtasks (due on or before yesterday and not completed)
        yesterday = today - timedelta(days=1)
        pending_subtasks = Subtask.objects.filter(task=task, due_date__lte=yesterday, completed=False)

        if subtasks.exists() or pending_subtasks.exists():
            today_tasks_list.append({'task': task, 'subtasks': subtasks, 'pending_subtasks': pending_subtasks})

    return render(request, 'today_tasks.html', {'today_tasks': today_tasks_list})

@login_required
def completed_tasks(request):
    completed_subtasks = Subtask.objects.filter(completed=True, task__user=request.user)
    completed_tasks_list = []
    for subtask in completed_subtasks:
        if subtask.task not in [item['task'] for item in completed_tasks_list]:
            completed_tasks_list.append({'task': subtask.task, 'subtasks': [subtask]})
        else:
            for item in completed_tasks_list:
                if item['task'] == subtask.task:
                    item['subtasks'].append(subtask)
                    break
    return render(request, 'completed_tasks.html', {'completed_tasks': completed_tasks_list})

from .forms import LoginForm, SignupForm, TaskForm

@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            priority = form.cleaned_data['priority']

            # Call Gemini API to generate title
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                title = "Default Title"
                print("GEMINI_API_KEY not found in environment variables.")
            else:
                try:
                    title = task_utils.generate_short_title(description, api_key)
                except Exception as e:
                    title = "Default Title"
                    print(f"Error generating title: {e}")

            task = Task.objects.create(user=request.user, description=description, title=title, start_date=start_date, due_date=end_date, priority=priority)

            # Call Gemini API to create subtasks
            subtasks_data = task_utils.break_down_task(description, str(start_date), str(end_date), priority, api_key)
            
            # Save subtasks to the database
            subtasks_data = task_utils.break_down_task(description, str(start_date), str(end_date), priority, api_key)
            
            # Save subtasks to the database
            for subtask_date, subtask_description in subtasks_data.items():
                subtask_date = datetime.strptime(subtask_date, "%Y-%m-%d").date()
                Subtask.objects.create(task=task, description=subtask_description, due_date=subtask_date)

            return redirect('all_tasks')
    else:
        form = TaskForm()
    return render(request, 'add_task.html', {'form': form})

@login_required
def task_breakdown(request):
    if request.method == 'POST':
        task_description = request.POST.get('task_description')
        start_date = request.POST.get('start_date')
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority')
        api_key = os.environ.get('GEMINI_API_KEY')

        try:
            subtasks = task_utils.break_down_task(task_description, start_date, due_date, priority, api_key)
            response_text = f"Task Breakdown:\n"
            for date, subtask in subtasks.items():
                response_text += f"{date}: {subtask}\n"
            return HttpResponse(response_text, content_type="text/plain")
        except Exception as e:
            return HttpResponse(f"Error: {e}", content_type="text/plain")
    else:
        return HttpResponse("Please submit a POST request with task_description, start_date, due_date, and priority.", content_type="text/plain")

@login_required
def redistribute_tasks_view(request):
    try:
        task_scheduler.main()
        return HttpResponse("Tasks redistributed successfully!", content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"Error redistributing tasks: {e}", content_type="text/plain")

@login_required
def complete_subtask(request, subtask_id):
    if request.method == 'POST':
        subtask = Subtask.objects.get(pk=subtask_id)
        subtask.completed = request.POST.get('completed') == 'True'
        subtask.save()
        return redirect('today_tasks')
    else:
        return HttpResponse("Invalid request method.", status=405)

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'account/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                print(f"Login successful for user: {username}")
                return redirect('all_tasks')
            else:
                print(f"Authentication failed for user: {username}")
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})

from django.contrib.auth.forms import PasswordResetForm

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Email sending logic here (omitted for brevity)
            return HttpResponse("Password reset email sent.")
    else:
        form = PasswordResetForm()
    return render(request, 'account/password_reset.html', {'form': form})

def about(request):
    return render(request, 'about.html')

@login_required
def task_detail(request, task_id):
    task = Task.objects.get(pk=task_id, user=request.user)
    subtasks = Subtask.objects.filter(task=task)
    return render(request, 'task_detail.html', {'task': task, 'subtasks': subtasks})

@login_required
def delete_task(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(pk=task_id, user=request.user)
        task.delete()
        return redirect('all_tasks')
    else:
        return HttpResponse("Invalid request method.", status=405)
