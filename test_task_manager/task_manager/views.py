from django.shortcuts import render, redirect
from django.http import HttpResponse
from . import task_utils
from . import task_scheduler
from .models import Task, Subtask
from datetime import date, timedelta, datetime
import os

def home(request):
    return render(request, 'home.html')

def all_tasks(request):
    tasks = Task.objects.all()
    for task in tasks:
        task.subtasks = Subtask.objects.filter(task=task)
        total_subtasks = task.subtasks.count()
        completed_subtasks = task.subtasks.filter(completed=True).count()
        if total_subtasks > 0:
            task.completion_percentage = (completed_subtasks / total_subtasks) * 100
        else:
            task.completion_percentage = 0
    return render(request, 'all_tasks.html', {'tasks': tasks})

def today_tasks(request):
    today = date.today()
    tasks = Task.objects.all()
    today_tasks_list = []
    for task in tasks:
        # Get today's subtasks
        subtasks = Subtask.objects.filter(task=task, due_date=today, completed=False)
        
        # Get pending subtasks (due before today and not completed)
        pending_subtasks = Subtask.objects.filter(task=task, due_date__lt=today, completed=False)

        if pending_subtasks.exists():
            # Reschedule pending subtasks
            api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyA7Vc7AXaVXz-W6ZBPOVhMgUretu1pPUWA')
            task_updates = task_scheduler.redistribute_tasks(task.description, list(pending_subtasks.values('description', 'due_date')), str(today), str(task.due_date), api_key)

            # Update subtasks with new due dates
            for subtask_date, subtask_description in task_updates.items():
                subtask_date = datetime.strptime(subtask_date, "%Y-%m-%d").date()
                try:
                    subtask = pending_subtasks.get(description=subtask_description)
                    subtask.due_date = subtask_date
                    subtask.save()
                except Subtask.DoesNotExist:
                    print(f"Subtask with description '{subtask_description}' not found.")

        if subtasks.exists() or pending_subtasks.exists():
            today_tasks_list.append({'task': task, 'subtasks': subtasks, 'pending_subtasks': pending_subtasks})

    return render(request, 'today_tasks.html', {'today_tasks': today_tasks_list})

def completed_tasks(request):
    completed_subtasks = Subtask.objects.filter(completed=True)
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

def add_task(request):
    if request.method == 'POST':
        description = request.POST['description']
        start_date = request.POST['start_date']
        due_date = request.POST['due_date']
        priority = request.POST['priority']

        # Call Gemini API to generate title
        api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyA7Vc7AXaVXz-W6ZBPOVhMgUretu1pPUWA')  # Replace with your actual API key or environment variable
        try:
            title = task_utils.generate_short_title(description, api_key)
        except Exception as e:
            title = "Default Title"
            print(f"Error generating title: {e}")

        task = Task.objects.create(description=description, title=title, start_date=start_date, due_date=due_date, priority=priority)

        # Call Gemini API to create subtasks
        subtasks_data = task_utils.break_down_task(description, str(start_date), str(due_date), priority, api_key)

        # Save subtasks to the database
        for subtask_date, subtask_description in subtasks_data.items():
            subtask_date = datetime.strptime(subtask_date, "%Y-%m-%d").date()
            Subtask.objects.create(task=task, description=subtask_description, due_date=subtask_date)

        return redirect('all_tasks')  # Redirect to the all_tasks page after adding a task
    else:
        return render(request, 'add_task.html')

def task_breakdown(request):
    if request.method == 'POST':
        task_description = request.POST.get('task_description')
        start_date = request.POST.get('start_date')
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority')
        api_key = "AIzaSyA7Vc7AXaVXz-W6ZBPOVhMgUretu1pPUWA" # Replace with your actual API key

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

def redistribute_tasks_view(request):
    try:
        task_scheduler.main()
        return HttpResponse("Tasks redistributed successfully!", content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"Error redistributing tasks: {e}", content_type="text/plain")

def complete_subtask(request, subtask_id):
    if request.method == 'POST':
        subtask = Subtask.objects.get(pk=subtask_id)
        subtask.completed = request.POST.get('completed') == 'True'
        subtask.save()
        return redirect('today_tasks')
    else:
        return HttpResponse("Invalid request method.", status=405)

def task_detail(request, task_id):
    task = Task.objects.get(pk=task_id)
    subtasks = Subtask.objects.filter(task=task)
    return render(request, 'task_detail.html', {'task': task, 'subtasks': subtasks})

def delete_task(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(pk=task_id)
        task.delete()
        return redirect('all_tasks')
    else:
        return HttpResponse("Invalid request method.", status=405)
