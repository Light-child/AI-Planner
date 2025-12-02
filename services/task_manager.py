import os
import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials 
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json_manager
from calender_manager import CalendarManager
from db import *

# --- Configuration Constants ---
# NOTE: Replace 'YOUR_TIMEZONE' with an actual timezone string like 'America/New_York'
TIME_ZONE = 'America/Los_Angeles' 
# The file path used to store the mapping between Task IDs and Event IDs
LINK_DATA_FILE = 'linked_tasks.json'

SCOPES = ["https://www.googleapis.com/auth/calendar", 'https://www.googleapis.com/auth/tasks']
class TaskManager:
        
    def __init__(self):
        print("Initializing TaskManager...")
        token_path = "C:/Users/Temidayo Adeaga/Documents/Work/AI planer/venv/token.json"
        if os.path.exists(token_path):
            print("token found.")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        else:
            print("token.json not found.")
            return            
        # 1. Initialize Google API Services
        # Assuming necessary scopes ('calendar', 'tasks') are in the credentials
        self.tasks_service: Resource = build('tasks', 'v1', credentials=creds)

        
        # 2. Initialize Local Data Store
        # Stores the mapping: {task_id: {event_id, calendar_id, task_list_id}}
        self.linked_tasks: dict = self._load_links()
        
        print(f"Loaded {len(self.linked_tasks)} linked tasks from {LINK_DATA_FILE}.")

  
    def create_task(self,task_body,task_list_id):
        # event_result = self.calendar_service.events().insert(calendarId=calendar_id, body=event_body).execute()
        task_result = self.tasks_service.tasks().insert(tasklist=task_list_id, body=task_body).execute()
        print("event created")

    def link_with_event(self):
        pass

    def create_linked_task_and_event(self, task_title: str, start_datetime: datetime, 
                                     duration_hours: float, rrule: str = None, 
                                     task_list_id: str = '@me', calendar_id: str = 'primary'):
        """
        Creates a Google Task and a linked Calendar Event (single or recurring).
        
        Args:
            task_title: The title of the task/event.
            start_datetime: The starting date and time of the first event instance.
            duration_hours: The duration of the event in hours.
            rrule: The RFC 5545 RRULE string for recurring events (e.g., 'RRULE:FREQ=WEEKLY;INTERVAL=1'). 
                   If None, a single event is created.
            task_list_id: The ID of the task list (default is primary '@me').
            calendar_id: The ID of the calendar (default is primary 'primary').
            
        Returns:
            A tuple of (task_id, event_id) or None on failure.
        """
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        try:
            # 1. Create the Google Task
            task_body = {
                'title': task_title,
                # Tasks API uses RFC 3339 timestamp for due date
                'due': start_datetime.isoformat() + 'Z' 
            }
            task_result = self.tasks_service.tasks().insert(tasklist=task_list_id, body=task_body).execute()
            task_id = task_result['id']

            # 2. Create the Google Calendar Event
            event_body = {
                'summary': f'[TASK] {task_title}',
                'start': {'dateTime': start_datetime.isoformat(), 'timeZone': TIME_ZONE},
                'end': {'dateTime': end_datetime.isoformat(), 'timeZone': TIME_ZONE},
                'description': f'Linked to Google Task ID: {task_id}. The series will be deleted when the task is completed.',
                # Add recurrence if RRULE is provided
                'recurrence': [rrule] if rrule else None
            }
            
            event_result = self.calendar_service.events().insert(calendarId=calendar_id, body=event_body).execute()
            event_id = event_result['id']

            # 3. Store the link locally and save
            self.linked_tasks[task_id] = {
                'event_id': event_id,
                'calendar_id': calendar_id,
                'task_list_id': task_list_id
            }
            self._save_links()
            
            print(f"Success: Created Task (ID: {task_id}) and Event (ID: {event_id})")
            return task_id, event_id

        except HttpError as e:
            print(f"An API error occurred during creation: {e}")
            return None, None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None, None

    def synchronize_tasks_and_events(self):
        """
        The core synchronization loop. Checks all linked tasks for completion 
        and deletes the corresponding Calendar event series if the task is done.
        This function should be run on a schedule (e.g., daily cron job).
        """
        print(f"\n--- Starting Synchronization Check ({datetime.now().isoformat()}) ---")
        tasks_to_remove = []
        
        # We iterate over a copy of the dictionary to safely modify the original
        for task_id, link_info in list(self.linked_tasks.items()):
            event_id = link_info['event_id']
            calendar_id = link_info['calendar_id']
            task_list_id = link_info['task_list_id']
            
            print(f"Checking Task ID: {task_id} (Event ID: {event_id})...")

            try:
                # 1. Fetch the Google Task details
                task = self.tasks_service.tasks().get(tasklist=task_list_id, task=task_id).execute()
                task_title = task.get('title', 'Unknown Task')
                status = task.get('status')
                
                # 2. Check for completion status
                if status == 'completed':
                    print(f"-> Task '{task_title}' is COMPLETED. Deleting linked event series.")
                    
                    # 3. Delete the Calendar Event Series
                    try:
                        # Deleting the parent event_id deletes the entire recurring series
                        self.calendar_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                        print(f"-> Successfully deleted Calendar Event Series.")
                    except HttpError as e:
                        # Event might have been manually deleted, check error code
                        if e.resp.status == 404:
                            print("-> Calendar Event already deleted or not found.")
                        else:
                            print(f"-> ERROR deleting event {event_id}: {e}")
                    
                    # 4. Mark the link for removal from local store
                    tasks_to_remove.append(task_id)

                else:
                    print(f"-> Task '{task_title}' is still '{status}'. No action needed.")

            except HttpError as e:
                # Handle 404: Task may have been manually deleted by the user
                if e.resp.status == 404:
                    print(f"-> Task ID {task_id} not found on Google Tasks. Cleaning up link.")
                    tasks_to_remove.append(task_id)
                else:
                    print(f"-> API Error checking task {task_id}: {e}")
            except Exception as e:
                print(f"-> Unexpected error during check: {e}")
        
        # 5. Clean up the local data store
        if tasks_to_remove:
            for task_id in tasks_to_remove:
                if task_id in self.linked_tasks:
                    del self.linked_tasks[task_id]
                    print(f"Removed Task ID {task_id} from local store.")
            self._save_links()
        
        print(f"--- Synchronization Complete. {len(self.linked_tasks)} tasks remaining. ---\n")
    def print_all_tasks(self):
        if not self.tasks_service:
            print("Cannot list tasks: Service not initialized.")
            return

        print("\n--- Listing All Tasks ---")

        try:
            # 1. Get the list of all task lists (e.g., "My Tasks", "Shopping List")
            
            tasklists_result = self.tasks_service.tasklists().list().execute()
            # print("Tasklists_ result")
            # print("_____")
            # print()
            # print(type(tasklists_result))
            # print(tasklists_result)

            tasklists = tasklists_result.get('items', [])
            # print("tasklists")
            # print("_____")
            # print(type(tasklists_result))
            # print(tasklists)

            if not tasklists:
                print("No task lists found.")
                return

            for tasklist in tasklists:
                list_id = tasklist['id']
                list_title = tasklist['title']
                
                print(f"\n[{list_title}]")
                print("=" * (len(list_title) + 2))
                
                # 2. Get the tasks for the current task list
                tasks_result = self.tasks_service.tasks().list(
                    tasklist=list_id,
                    showCompleted=True, # Include completed tasks
                    showHidden=True     # Include hidden tasks
                ).execute()
                print(tasks_result)
                tasks = tasks_result.get('items', [])

                if not tasks:
                    print("  (Empty list or no uncompleted tasks.)")
                    continue
                
                for task in tasks:
                    status = "✅" if task.get('status') == 'completed' else "⬜"
                    title = task.get('title', 'Untitled Task')
                    
                    # Print in the format: [Status] Title (Due Date if exists)
                    due_date = task.get('due')
                    if due_date:
                        # Simple cleanup for display
                        due_date = due_date.split('T')[0]
                        print(f"  {status} {title} (Due: {due_date})")
                    else:
                        print(f"  {status} {title}")

        except HttpError as err:
            print(f"An HTTP error occurred: {err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    
    # wrote this myself
    def delete_task(self, task_id, tasklist_id):

        self.tasks_service.tasks().delete(
            tasklist=tasklist_id,
            task=task_id
        ).execute()
        events  = db.get_event_by_task_id(task_id)
        for event in events:
            event_id, calendar_id = event
            CalendarManager().delete_event(event_id, calendar_id, True)
        db.delete_task_id("task_id")
     
    def complete_task(self):
        pass
        


if __name__ == '__main__':
    task = TaskManager()
    # task.create_task('test', 'MTYxNDI4NDc4MDkwMjIzOTM0ODY6MDow')
    # task.print_all_tasks()
    body = {
    'title': 'TEST',
    'notes': 'TEST',
    'due': '2025-11-01T12:00:00.000Z', 
    'status': 'needsAction'
    }
    task.create_task( body, 'MTYxNDI4NDc4MDkwMjIzOTM0ODY6MDow')
