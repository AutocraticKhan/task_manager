import json
import requests
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

def generate_short_title(task_description, api_key):
    """
    Generate a short title for a task using Gemini AI.

    Args:
        task_description (str): The full task description
        api_key (str): Google API key for Gemini

    Returns:
        str: A short title for the task
    """
    # Create the prompt to send to Gemini
    prompt = f"""
    Please generate a short, concise title (maximum 5 words) for the following task description.
    The title should be descriptive but brief, with no punctuation at the end.

    Task description: {task_description}

    Provide ONLY the title with no additional text or explanation.
    """

    # Prepare the API request
    api_key = os.environ.get('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    # Make the API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check if the request was successful
    if response.status_code != 200:
        # If API call fails, create a simple title from the task description
        words = task_description.split()
        if len(words) <= 5:
            return task_description.replace(",", "")
        else:
            return " ".join(words[:5]).replace(",", "")
    
    # Process the response
    try:
        response_data = response.json()
        
        # Extract the generated text from the response
        if 'candidates' in response_data and response_data['candidates']:
            text_content = ""
            for candidate in response_data['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            text_content += part['text']
            
            # Clean up the response
            short_title = text_content.strip().replace("\n", " ").replace(",", "")
            
            # Limit to 5 words if longer
            words = short_title.split()
            if len(words) > 5:
                short_title = " ".join(words[:5])
            
            return short_title
        else:
            raise Exception("No content in API response")
            
    except Exception as e:
        # If parsing fails, create a simple title from the task description
        words = task_description.split()
        if len(words) <= 5:
            return task_description.replace(",", "")
        else:
            return " ".join(words[:5]).replace(",", "")

def break_down_task(task_description, start_date_str, due_date_str, priority, api_key):
    """
    Break down a task into smaller chunks from start date until the due date using Gemini AI.
    
    Args:
        task_description (str): Brief description of the task
        start_date_str (str): Start date in YYYY-MM-DD format
        due_date_str (str): Due date in YYYY-MM-DD format
        priority (str): Priority level (High, Medium, Low)
        api_key (str): Google API key for Gemini
    
    Returns:
        dict: Dictionary of dates and corresponding subtasks with status
    """
    # Parse dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    
    if due_date < start_date:
        raise ValueError("Due date must be after start date")
    
    days_until_due = (due_date - start_date).days + 1  # Include both start and end day
    if days_until_due < 1:
        days_until_due = 1  # At least one day for task breakdown
    
    # Create the prompt to send to Gemini
    next_day_str = (start_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    prompt = f"""
    Task: {task_description}
    Priority: {priority}
    Start date: {start_date_str}
    Due date: {due_date_str}
    Days available: {days_until_due}
    
    Break down this task into {min(days_until_due, 10)} logical sequential subtasks, with one subtask per day,
    starting from the start date ({start_date_str}) until the due date ({due_date_str}).
    
    Format your response as a JSON object with dates as keys (in YYYY-MM-DD format) and subtasks as values.
    The dates MUST be between {start_date_str} and {due_date_str} inclusive.
    Provide short, clear subtask descriptions that don't contain commas to avoid CSV parsing issues.
    
    Example format:
    {{
        "{start_date_str}": "Research topic outline",
        "{next_day_str}": "Create initial draft",
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

    # Make the API request
    response = requests.post(url, headers=headers, json=data)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Process the response
    try:
        response_data = response.json()

        # Extract the generated text from the response
        if 'candidates' in response_data and response_data['candidates']:
            text_content = ""
            for candidate in response_data['candidates']:
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            text_content += part['text']

            # Clean up the response
            short_title = text_content.strip().replace("\n", " ").replace(",", "")

            # Limit to 5 words if longer
            words = short_title.split()
            if len(words) > 5:
                short_title = " ".join(words[:5])

            return short_title
        else:
            raise Exception("No content in API response")

    except Exception as e:
        # If parsing fails, create a simple title from the task description
        words = task_description.split()
        if len(words) <= 5:
            return task_description.replace(",", "")
        else:
            return " ".join(words[:5]).replace(",", "")

def break_down_task(task_description, start_date_str, due_date_str, priority, api_key):
    """
    Break down a task into smaller chunks from start date until the due date using Gemini AI.

    Args:
        task_description (str): Brief description of the task
        start_date_str (str): Start date in YYYY-MM-DD format
        due_date_str (str): Due date in YYYY-MM-DD format
        priority (str): Priority level (High, Medium, Low)
        api_key (str): Google API key for Gemini

    Returns:
        dict: Dictionary of dates and corresponding subtasks with status
    """
    # Parse dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

    if due_date < start_date:
        raise ValueError("Due date must be after start date")

    days_until_due = (due_date - start_date).days + 1  # Include both start and end day
    if days_until_due < 1:
        days_until_due = 1  # At least one day for task breakdown

    # Create the prompt to send to Gemini
    next_day_str = (start_date + timedelta(days=1)).strftime('%Y-%m-%d')

    prompt = f"""
    Task: {task_description}
    Priority: {priority}
    Start date: {start_date_str}
    Due date: {due_date_str}
    Days available: {days_until_due}

    Break down this task into {min(days_until_due, 10)} logical sequential subtasks, with one subtask per day,
    starting from the start date ({start_date_str}) until the due date ({due_date_str}).

    Format your response as a JSON object with dates as keys (in YYYY-MM-DD format) and subtasks as values.
    The dates MUST be between {start_date_str} and {due_date_str} inclusive.
    Provide short, clear subtask descriptions that don't contain commas to avoid CSV parsing issues.

    Example format:
    {{
        "{start_date_str}": "Research topic outline",
        "{next_day_str}": "Create initial draft",
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

    # Make the API request
    response = requests.post(url, headers=headers, json=data)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Process the response
    try:
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
                # Create properly dated subtasks manually
                raise Exception("API returned invalid dates")
        else:
            raise Exception("No content in API response")

    except Exception as e:
        # If parsing fails or dates are invalid, create a basic breakdown manually
        subtasks = {}
        current_date = start_date

        # Generate dates between start date and due date
        date_range = []
        temp_date = current_date
        while temp_date <= due_date:
            date_range.append(temp_date)
            temp_date += timedelta(days=1)

        # Create appropriate number of subtasks
        num_dates = len(date_range)

        if num_dates == 1:
            # Only one day available
            subtasks[date_range[0].strftime("%Y-%m-%d")] = f"Complete {task_description}"
        elif num_dates == 2:
            # Two days available
            subtasks[date_range[0].strftime("%Y-%m-%d")] = f"Research & plan {task_description}"
            subtasks[date_range[1].strftime("%Y-%m-%d")] = f"Complete {task_description}"
        elif num_dates == 3:
            # Three days available
            subtasks[date_range[0].strftime("%Y-%m-%d")] = f"Research & outline {task_description}"
            subtasks[date_range[1].strftime("%Y-%m-%d")] = f"Draft {task_description}"
            subtasks[date_range[2].strftime("%Y-%m-%d")] = f"Finalize {task_description}"
        else:
            # More than three days
            subtasks[date_range[0].strftime("%Y-%m-%d")] = f"Research for {task_description}"

            # Middle days
            middle_dates = date_range[1:-1]
            middle_count = len(middle_dates)

            if task_description.lower().startswith("write") or "report" in task_description.lower() or "essay" in task_description.lower():
                # Writing-oriented task
                if middle_count >= 3:
                    research_end = min(middle_count // 3, 2)
                    drafting_end = min(2 * (middle_count // 3), middle_count - 1)

                    # Research phase
                    for i in range(research_end):
                        subtasks[middle_dates[i].strftime("%Y-%m-%d")] = f"Research part {i+1} for {task_description}"

                    # Drafting phase
                    for i in range(research_end, drafting_end):
                        subtasks[middle_dates[i].strftime("%Y-%m-%d")] = f"Draft section {i-research_end+1} of {task_description}"

                    # Refining phase
                    for i in range(drafting_end, middle_count):
                        subtasks[middle_dates[i].strftime("%Y-%m-%d")] = f"Edit part {i-drafting_end+1} of {task_description}"
                else:
                    # Fewer middle days
                    for i, date in enumerate(middle_dates):
                        subtasks[date.strftime("%Y-%m-%d")] = f"Continue part {i+1} of {task_description}"
            else:
                # Generic task
                for i, date in enumerate(middle_dates):
                    subtasks[date.strftime("%Y-%m-%d")] = f"Step {i+2}: {task_description}"

            # Final day
            subtasks[date_range[-1].strftime("%Y-%m-%d")] = f"Finalize {task_description}"

        return subtasks

def save_task_to_csv(task_name, subtasks, short_title, filename="tasks.csv"):
    """
    Save the task breakdown to a CSV file, including a status column for each task.
    
    Args:
        task_name (str): Name of the task (for reference)
        subtasks (dict): Dictionary of dates and corresponding subtasks
        short_title (str): Short title to use as the CSV column header
        filename (str): Name of the CSV file
    """
    # Clean short title to avoid issues with CSV headers
    clean_short_title = short_title.replace(",", ";").strip()
    status_title = f"{clean_short_title} Status"
    
    # Data structure to hold all CSV data
    all_data = {}
    all_task_names = set(["Date"])  # Always include Date column
    
    # Read existing CSV if it exists
    if os.path.exists(filename):
        try:
            with open(filename, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader, [])  # Get the headers
                
                if not headers:
                    headers = ["Date"]
                
                # Extract all task names (column headers)
                for header in headers:
                    all_task_names.add(header)
                
                # Read data rows
                for row in reader:
                    if not row:  # Skip empty rows
                        continue
                    
                    if len(row) >= 1:  # Ensure there's at least a date
                        date = row[0]
                        all_data[date] = {}
                        
                        # Map each column value to its header
                        for i, value in enumerate(row):
                            if i < len(headers):
                                all_data[date][headers[i]] = value
        except Exception as e:
            print(f"Warning: Error reading existing CSV file: {e}")
            all_data = {}
    
    # Add the new task name and status column to the set of all task names
    all_task_names.add(clean_short_title)
    all_task_names.add(status_title)
    
    # Update data with new subtasks and their status
    for date, subtask in subtasks.items():
        if date not in all_data:
            all_data[date] = {"Date": date}
        
        all_data[date][clean_short_title] = subtask
        all_data[date][status_title] = "Pending"  # Default status
    
    # Convert set of task names to ordered list, ensuring "Date" is first and status columns follow task columns
    task_columns = []
    status_columns = []
    
    for header in all_task_names:
        if header == "Date":
            continue
        elif header.endswith(" Status"):
            status_columns.append(header)
        else:
            task_columns.append(header)
    
    # Group task columns with their status columns
    ordered_columns = []
    for task in sorted(task_columns):
        ordered_columns.append(task)
        status_col = f"{task} Status"
        if status_col in status_columns:
            ordered_columns.append(status_col)
    
    all_headers = ["Date"] + ordered_columns
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(all_headers)
            
            # Write data rows
            for date in sorted(all_data.keys()):
                row = []
                for header in all_headers:
                    row.append(all_data[date].get(header, ""))
                writer.writerow(row)
        
        print(f"Task breakdown saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    # Replace with your API key
    GEMINI_API_KEY = "AIzaSyA7Vc7AXaVXz-W6ZBPOVhMgUretu1pPUWA"
    
    # Get task details
    task = input("Enter task description: ")
    
    # Get initial date with today as default
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_date = input(f"Enter start date (YYYY-MM-DD) [default: {today_str}]: ")
    if not start_date.strip():
        start_date = today_str
        
    due_date = input("Enter due date (YYYY-MM-DD): ")
    priority = input("Enter priority (High/Medium/Low): ")
    
    try:
        # Generate short title using Gemini API
        short_title = generate_short_title(task, GEMINI_API_KEY)
        print(f"Generated column title: {short_title}")
        
        # Get the breakdown
        subtasks = break_down_task(task,start_date, due_date, priority, GEMINI_API_KEY)
        
        # Print the breakdown
        print(f"\nTask: {task} (Priority: {priority})")
        print(f"Due date: {due_date}\n")
        print("Daily Breakdown:")
        
        # Loop through and print each subtask by date
        for date, subtask in sorted(subtasks.items()):
            print(f"{date}: {subtask}")
        
        # Save to CSV with the short title
        save_task_to_csv(task, subtasks, short_title)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
