import json
import requests
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

def get_pending_tasks(csv_file):
    """
    Get all pending tasks up to the current date from the CSV file.
    
    Args:
        csv_file (str): Path to the CSV file
        
    Returns:
        dict: Dictionary with task names as keys and lists of pending subtasks as values
        dict: Dictionary with task names as keys and their specific due dates as values
    """
    today = datetime.now().date()
    pending_tasks = defaultdict(list)
    task_due_dates = {}
    
    try:
        with open(csv_file, 'r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)
            
            # Get task name columns and their corresponding status columns
            tasks = {}
            for i, header in enumerate(headers):
                if header != "Date" and not header.endswith(" Status"):
                    # Find the status column for this task
                    status_col = f"{header} Status"
                    if status_col in headers:
                        status_index = headers.index(status_col)
                        tasks[header] = {"index": i, "status_index": status_index}
            
            # Initialize empty lists to track dates for each task
            task_dates = {task_name: [] for task_name in tasks.keys()}
            
            # Process data rows
            for row in reader:
                if not row or len(row) < len(headers):
                    continue
                
                date_str = row[0]
                try:
                    row_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # Process each task in the row
                    for task_name, indices in tasks.items():
                        task_index = indices["index"]
                        status_index = indices["status_index"]
                        
                        # Check if task has content (to track valid dates for this task)
                        if task_index < len(row) and row[task_index]:
                            task_dates[task_name].append(row_date)
                        
                        # Only consider rows up to today for pending tasks
                        if row_date <= today and task_index < len(row) and status_index < len(row):
                            task_description = row[task_index]
                            task_status = row[status_index]
                            
                            # If there's a task and it's pending
                            if task_description and task_status == "Pending":
                                pending_tasks[task_name].append({
                                    "date": date_str,
                                    "description": task_description
                                })
                except ValueError:
                    continue
            
            # Set due dates as the latest date in the CSV for each specific task
            for task_name, dates in task_dates.items():
                if dates:
                    # Set the due date as the latest date where this task has an entry
                    max_date = max(dates)
                    task_due_dates[task_name] = max_date.strftime("%Y-%m-%d")
                    
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return pending_tasks, task_due_dates

def redistribute_tasks(task_name, pending_subtasks, start_date_str, due_date_str, api_key):
    """
    Redistribute pending tasks across remaining days using Gemini API.
    
    Args:
        task_name (str): Name of the task
        pending_subtasks (list): List of pending subtasks
        start_date_str (str): Start date in YYYY-MM-DD format (today)
        due_date_str (str): Due date in YYYY-MM-DD format
        api_key (str): Google API key for Gemini
        
    Returns:
        dict: Dictionary of dates and corresponding redistributed subtasks
    """
    # Parse dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    
    if due_date < start_date:
        print(f"Warning: Due date {due_date_str} is before start date {start_date_str} for task {task_name}")
        return {}
    
    days_until_due = (due_date - start_date).days + 1  # Include both start and end days
    
    if days_until_due < 1:
        print(f"No days left to redistribute tasks for {task_name}")
        return {}
    
    # Format pending tasks for the prompt
    pending_tasks_formatted = "\n".join([f"- {task['date']}: {task['description']}" for task in pending_subtasks])
    
    # Create the prompt for Gemini
    prompt = f"""
    TASK: {task_name}
    
    PENDING SUBTASKS (need to be rescheduled):
    {pending_tasks_formatted}
    
    START DATE: {start_date_str} (today)
    DUE DATE: {due_date_str}
    DAYS AVAILABLE: {days_until_due}
    
    Need to redistribute ALL pending subtasks plus complete the original task by the due date.
    Break this down into {days_until_due} logical sequential subtasks, with one subtask per day,
    starting from today ({start_date_str}) until the due date ({due_date_str}).
    
    Format your response as a JSON object with dates as keys (in YYYY-MM-DD format) and subtasks as values.
    The dates MUST be between {start_date_str} and {due_date_str} inclusive.
    Provide short, clear subtask descriptions that don't contain commas to avoid CSV parsing issues.
    
    Example format:
    {{
        "{start_date_str}": "Complete pending research and draft outline",
        "{(start_date + timedelta(days=1)).strftime('%Y-%m-%d')}": "Finish first draft",
        ...
    }}
    
    IMPORTANT: Make sure all dates are within the correct range from {start_date_str} to {due_date_str}.
    """
    
    # Prepare the API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")
        
        # Process the response
        response_data = response.json()
        
        # Extract the generated text from the response
        if 'candidates' in response_data and response_data['candidates']:
            text_content = ""
            for candidate in response_data['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            text_content += part['text']
            
            # Extract JSON from the text response
            json_part = text_content.strip()
            if json_part.startswith("```json"):
                json_part = json_part.split("```json")[1].split("```")[0].strip()
            elif json_part.startswith("```"):
                json_part = json_part.split("```")[1].split("```")[0].strip()
                
            subtasks = json.loads(json_part)
            
            # Validate dates to ensure they're in the correct range
            valid_dates = True
            for date_str in subtasks.keys():
                try:
                    task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if task_date < start_date or task_date > due_date:
                        valid_dates = False
                        break
                except ValueError:
                    valid_dates = False
                    break
            
            if valid_dates:
                # Replace any commas in subtask descriptions to avoid CSV parsing issues
                for date, description in subtasks.items():
                    subtasks[date] = description.replace(",", ";")
                return subtasks
            else:
                raise Exception("API returned invalid dates")
        else:
            raise Exception("No content in API response")
            
    except Exception as e:
        print(f"Error with Gemini API for task {task_name}: {e}")
        
        # Create a fallback breakdown manually
        subtasks = {}
        current_date = start_date
        
        # If days available >= pending tasks + 1 (for final completion), distribute evenly
        if days_until_due >= len(pending_subtasks) + 1:
            for i, task in enumerate(pending_subtasks):
                subtasks[current_date.strftime("%Y-%m-%d")] = f"Complete: {task['description']}"
                current_date += timedelta(days=1)
            
            # Add final completion task
            remaining_days = (due_date - current_date).days
            if remaining_days > 0:
                mid_point = current_date + timedelta(days=remaining_days // 2)
                subtasks[mid_point.strftime("%Y-%m-%d")] = f"Progress check on {task_name}"
            
            subtasks[due_date.strftime("%Y-%m-%d")] = f"Finalize {task_name}"
        else:
            # Not enough days, need to combine tasks
            # Group pending tasks into chunks
            chunks = []
            pending_count = len(pending_subtasks)
            chunk_size = max(1, pending_count // (days_until_due - 1))
            
            for i in range(0, pending_count, chunk_size):
                chunk = pending_subtasks[i:i+chunk_size]
                descriptions = [item['description'] for item in chunk]
                chunks.append("; ".join(descriptions))
            
            # Assign chunks to days
            for i, chunk in enumerate(chunks):
                if current_date <= due_date:
                    subtasks[current_date.strftime("%Y-%m-%d")] = f"Catch-up: {chunk}"
                    current_date += timedelta(days=1)
            
            # Add final task if there's still time
            if current_date <= due_date:
                subtasks[due_date.strftime("%Y-%m-%d")] = f"Finalize {task_name}"
        
        return subtasks

def update_csv_with_redistributed_tasks(csv_file, task_updates):
    """
    Update the CSV file with redistributed tasks.
    
    Args:
        csv_file (str): Path to the CSV file
        task_updates (dict): Dictionary with task names as keys and redistributed subtasks as values
    """
    if not task_updates:
        print("No tasks to update.")
        return
    
    # Read the entire CSV into memory
    all_data = {}
    headers = []
    
    try:
        with open(csv_file, 'r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)
            
            # Read data rows
            for row in reader:
                if not row or len(row) < 1:
                    continue
                date = row[0]
                all_data[date] = row
    except Exception as e:
        print(f"Error reading CSV for update: {e}")
        return
    
    # For each task, update or add the redistributed subtasks
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    for task_name, subtasks in task_updates.items():
        # Find column indices for task and status
        task_index = -1
        status_index = -1
        
        for i, header in enumerate(headers):
            if header == task_name:
                task_index = i
            elif header == f"{task_name} Status":
                status_index = i
        
        if task_index == -1 or status_index == -1:
            print(f"Could not find columns for task: {task_name}")
            continue
        
        # Update the rows from today onwards
        for date, subtask in subtasks.items():
            if date not in all_data:
                # Create a new row with empty cells
                all_data[date] = [""] * len(headers)
                all_data[date][0] = date  # Set the date
            
            # Update task and status
            row = all_data[date]
            if len(row) <= max(task_index, status_index):
                # Extend row if needed
                row.extend([""] * (max(task_index, status_index) - len(row) + 1))
            
            row[task_index] = subtask
            row[status_index] = "Pending"
        
        # Mark any pending tasks before today as "Rescheduled"
        for date, row in all_data.items():
            try:
                row_date = datetime.strptime(date, "%Y-%m-%d").date()
                if row_date < datetime.now().date() and len(row) > status_index:
                    if row[task_index] and row[status_index] == "Pending":
                        row[status_index] = "Rescheduled"
            except ValueError:
                continue
    
    # Write updated data back to CSV
    try:
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            
            # Sort by date and write rows
            for date in sorted(all_data.keys()):
                writer.writerow(all_data[date])
        
        print(f"Successfully updated tasks in {csv_file}")
    except Exception as e:
        print(f"Error writing updated CSV: {e}")

def main():
    # Set your Gemini API key here
    GEMINI_API_KEY = "AIzaSyA7Vc7AXaVXz-W6ZBPOVhMgUretu1pPUWA"
    
    # CSV file path
    csv_file = "tasks.csv"
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found.")
        return
    
    # Get today's date
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    # Get pending tasks up to today
    pending_tasks, task_due_dates = get_pending_tasks(csv_file)
    
    if not pending_tasks:
        print("No pending tasks found to reschedule.")
        return
    
    print(f"Found {sum(len(tasks) for tasks in pending_tasks.values())} pending task(s) to reschedule")
    
    # Redistribute tasks for each task name
    task_updates = {}
    
    for task_name, subtasks in pending_tasks.items():
        if not subtasks:
            continue
            
        print(f"Rescheduling {len(subtasks)} subtasks for '{task_name}'")
        
        # Get due date for this task
        due_date = task_due_dates.get(task_name)
        if not due_date:
            print(f"No due date found for task {task_name}")
            continue
        
        # Redistribute tasks from today until due date
        redistributed = redistribute_tasks(task_name, subtasks, today, due_date, GEMINI_API_KEY)
        if redistributed:
            task_updates[task_name] = redistributed
            print(f"Successfully redistributed tasks for '{task_name}'")
    
    # Update the CSV with redistributed tasks
    if task_updates:
        update_csv_with_redistributed_tasks(csv_file, task_updates)
    else:
        print("No tasks were successfully redistributed.")

if __name__ == "__main__":
    main()
