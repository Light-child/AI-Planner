#All of Google CAlendar API Logic
# calendar_manager.py
import datetime as dt
import os
from datetime import timezone, timedelta
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
import re



# If modifying these scopes, delete the file token.json.z
# IMPORTANT: Make sure these scopes match what you configured in the Google Cloud Console
SCOPES = ["https://www.googleapis.com/auth/calendar", 'https://www.googleapis.com/auth/tasks'] # Added freebusy scope
class CalendarManager:
    def __init__(self):
        self.service= self.get_calendar_service()
    def get_calendar_service(self):
        creds = None
        # Check if token.json already exists
        if os.path.exists("backend/token.json"):
            creds = Credentials.from_authorized_user_file("backend/token.json", SCOPES)
        
        # If no valid credentials or expired, initiate the OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request()) # Refresh token if expired
            else:
                # This is the part that triggers the browser for initial authorization
                flow = InstalledAppFlow.from_client_secrets_file("C:/Users/Temidayo Adeaga/Documents/Work/AI planer/venv/backend/services/credentials.json", SCOPES)
                creds = flow.run_local_server(port=0) # This opens the browser
            # Save the new/refreshed credentials to token.json
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    # ... rest of your calendar_manager.py functions
    # You might also want functions to list events for testing purposes

    # def list_events(self, max_results=10):
    #     service = self.get_calendar_service()
    #     now = datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z' # 'Z' indicates UTC time
    #     events_result = service.events().list(
    #         calendarId='primary', timeMin=now, maxResults=max_results, singleEvents=True,
    #         orderBy='startTime').execute()
    #     events = events_result.get('items', [])
    #     if not events:
    #         print('No upcoming events found.')
    #         return []
    #     print('Upcoming events:')
    #     for event in events:
    #         start = event['start'].get('dateTime', event['start'].get('date'))
    #         print(f"{start} - {event['summary']}")
    #     return events
    
    #Under development
    def add_event(self,event_body):
        """
        Adds an event to the specified Google Calendar.
        Returns:
            dict: The created event resource if successful, None otherwise.
        """
        
        try:
            created_event = self.service.events().insert(body= event_body, calendarId='primary').execute()
            print(f"Event created: {created_event.get('htmlLink')}")
            return created_event

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
    def get_free_busy_slots(self, time_min: str, time_max: str) -> dict:
        """
        Queries the user's calendar for busy times within a given range.

        Args:
            time_min: The start time of the query range (ISO 8601 string).
            time_max: The end time of the query range (ISO 8601 string).

        Returns:
            A dictionary of free/busy data.
        """
        try:
            # Prepare the request body for the free/busy query
            body = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [
                    {"id": "primary"}  # Query the user's primary calendar
                ]
            }
            
            # Make the API call
            response = self.service.freebusy().query(body=body).execute()
            
            # The 'calendars' key contains the free/busy data for each queried calendar
            return response.get('calendars', {}).get('primary', {})
        
        except Exception as e:
            print(f"An error occurred while querying free/busy data: {e}")
            return {}
        
    def get_available_slots(self, time_min: str, time_max: str) -> list:
        """
        Orchestrates the process of getting busy data and calculating free slots.
        """
        # Step 1: Call the API to get busy data.
        busy_data = self.get_free_busy_slots(time_min, time_max)
        
        # Extract the list of busy time slots from the dictionary.
        busy_slots = busy_data.get('busy', [])
        
        # Step 2: Pass the list of busy slots to the calculation method.
        free_slots = self.calculate_free_slots(time_min, time_max, busy_slots)
        
        return free_slots
    
    def delete_event(self, event_id, calendar_id, one_time):
        """
        Deletes a single instance of an event or all occurrences of a recurring event.

        Args:
            event_id (str): The ID of the event or the recurring series ID.
            calendar_id (str): The ID of the calendar containing the event (e.g., 'primary').
            one_time (bool): 
                True: Deletes only one instance (requires event_id to be the instance ID).
                False: Deletes the entire recurring series (requires event_id to be the Series ID).
        """
        if one_time:
            # 1. DELETE A SINGLE INSTANCE (Requires the specific instance ID)
            # The API allows us to delete a specific instance by calling delete() 
            # with the instance's unique event ID.
            try:
                self.service.events().delete(
                    calendarId=calendar_id, 
                    eventId=event_id
                ).execute()
                print(f"Successfully deleted single event instance: {event_id} from {calendar_id}.")
                return True
            except HttpError as err:
                # Handle 404 Not Found, which often occurs if the instance was already deleted
                if err.resp.status == 404:
                    print(f"Instance {event_id} not found. May have been previously deleted.")
                    return False
                print(f"Error deleting single instance {event_id}: {err}")
                return False

    def print_all_events(self):
        """
        Fetches and prints the original event definitions (including recurring series) 
        from all calendars, without time limits or instance expansion.
        
        Recurring events will appear once, showing their recurrence rule (RRULE).
        """

        if not self.service:
            print("Cannot list events: Service not initialized.")
            return

        print("\n--- Listing All Event Definitions (Recurring Series Only Once) ---")
        
        # NOTE: We remove timeMin/timeMax for a broad query and remove singleEvents=True 
        # to fetch the original recurring event definitions, which includes the RRULE.
        
        try:
            # 1. Get the list of all calendars (similar to getting all tasklists)
            calendar_list_result = self.service.calendarList().list().execute()
            calendars = calendar_list_result.get('items', [])
            
            if not calendars:
                print("No calendars found for this account.")
                return

            for calendar in calendars:
                if calendar['summary'] == 'posaldis99@gmail.com':
                    calendar_id = calendar['id']
                    calendar_title = calendar['summary']
                    
                    print(f"\n[{calendar_title}]")
                    print(f"\n[{calendar_id}]")

                    print("=" * (len(calendar_title) + 2))
                    
                    # 2. Get the events for the current calendar
                    events_result = self.service.events().list(
                        calendarId=calendar_id, 
                        # Removed timeMin/timeMax for no time limit
                        # Removed singleEvents=True to get the recurring event "blueprint"
                        singleEvents = True,
            
                    ).execute()
                    
                    events = events_result.get('items', [])
                    print(events)
                else:
                    continue
                if not events:
                    print("  (No events found.)")
                    continue
                
                for event in events:
                    summary = event.get('summary', 'No Title')
                    
                    # Check for recurrence information (RRULE)
                    recurrence_rules = event.get('recurrence')
                    
                    # Get the start time information (date or dateTime)
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    
                    if recurrence_rules:
                        # This is a recurring series definition
                        rule_str = ", ".join(recurrence_rules)
                        print(f"  🔁 SERIES: {summary} (ID: {event['id']})")
                        print(f"    - Starts: {start}")
                        print(f"    - Rule: {rule_str}")
                    else:
                        # This is a one-time event
                        print(f"  ✅ ONE-TIME: {summary} (ID: {event['id']})")
                        print(f"    - Starts: {start}")

        except HttpError as err:
            print(f"An HTTP error occurred: {err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    def get_info(self, summary): 
        """
        returns a list of calender id and info of an event as a dcitionary
        Sample:
        {
            "kind": "calendar#event",
            "etag": '"3513140602917502"',
            "id": "78ol5qnfhbh46tvcsqbub0uqoo",
            "status": "confirmed",
            "htmlLink": "https://www.google.com/calendar/event?eid=NzhvbDVxbmZoYmg0NnR2Y3NxYnViMHVxb29fMjAyNTA5MDJUMTMwMDAwWiBwb3NhbGRpczk5QG0",
            "created": "2025-08-30T16:11:41.000Z",
            "updated": "2025-08-30T16:11:41.458Z",
            "summary": "Breakfast event",
            "description": "Breakfast event on Tuesday",
            "creator": {"email": "posaldis99@gmail.com", "self": True},
            "organizer": {"email": "posaldis99@gmail.com", "self": True},
            "start": {
                "dateTime": "2025-09-02T08:00:00-05:00",
                "timeZone": "America/Chicago",
            },
            "end": {
                "dateTime": "2025-09-02T09:00:00-05:00",
                "timeZone": "America/Chicago",
            },
            "recurrence": ["RRULE:FREQ=WEEKLY;UNTIL=20251231T235959Z;BYDAY=TU"],
            "iCalUID": "78ol5qnfhbh46tvcsqbub0uqoo@google.com",
            "sequence": 0,
            "reminders": {"useDefault": True},
            "eventType": "default",
        }
        """

        if not self.service:
            print("Cannot list events: Service not initialized.")
            return

        print("\n--- Listing All Event Definitions (Recurring Series Only Once) ---")
        
        # NOTE: We remove timeMin/timeMax for a broad query and remove singleEvents=True 
        # to fetch the original recurring event definitions, which includes the RRULE.
        
        try:
            # 1. Get the list of all calendars (similar to getting all tasklists)
            calendar_list_result = self.service.calendarList().list().execute()
            calendars = calendar_list_result.get('items', [])
            
            if not calendars:
                print("No calendars found for this account.")
                return

            for calendar in calendars:
                calendar_id = calendar['id']
                calendar_title = calendar['summary']
                
                print(f"\n[{calendar_title}]")
                print("=" * (len(calendar_title) + 2))
                
                # 2. Get the events for the current calendar
                events_result = self.service.events().list(
                    calendarId=calendar_id, 
                    # Removed timeMin/timeMax for no time limit
                    # Removed singleEvents=True to get the recurring event "blueprint"
        
                ).execute()
                
                events = events_result.get('items', [])

                if not events:
                    print("  (No events found.)")
                    continue
                
                for event in events:
                    if event["summary"] == summary:
                        return [calendar_id,event]
            print("No event with This summary found.")
        except HttpError as err:
            print(f"An HTTP error occurred: {err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    def get_timezone(self): 
        timezone_setting = self.service.settings().get(setting='timezone').execute()
        user_timezone = timezone_setting.get("value")
        return user_timezone
    
    def calculate_weekly_stats(self, start_date_iso, end_date_iso, calendar_id='primary'):
        """
        Analyzes all events for a week and aggregates time spent per category.

        Args:
            calendar_service: The authenticated Google Calendar API service object.
            start_date_iso (str): Start date/time in ISO format (e.g., '2025-11-01T00:00:00Z').
            end_date_iso (str): End date/time in ISO format.
            calendar_id (str): The calendar ID to analyze.

        Returns:
            dict: Total time spent in hours for each category.
        """
        CATEGORY_KEYWORDS = {
        'Sleep': ['Sleep', 'Nap', 'Rest', 'Asleep'],
        'Work': ['Work', 'Meeting', 'Client', 'Project', 'Sprint', 'Standup'],
        'Leisure': ['Gym', 'Workout', 'Hobby', 'Reading', 'Movie', 'Personal Project', 'Run'],
        # Any event not matching the above will fall into the 'Other' category.
        }


        total_time_spent = {cat: timedelta(0) for cat in CATEGORY_KEYWORDS}
        total_time_spent['Other'] = timedelta(0)
        
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id, 
                timeMin=start_date_iso,
                timeMax=end_date_iso,
                singleEvents=True, # Essential for counting every instance of a recurring event
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
        except HttpError as err:
            print(f"Error fetching events for stats: {err}")
            return {k: 0 for k in total_time_spent}

        for event in events:
            summary = event.get('summary', '').lower()
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            
            # Skip all-day events and events without clear start/end times
            if not start or not end:
                continue

            try:
                # Parse times with robust handling for timezones (crucial for duration)
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                duration = end_dt - start_dt
            except ValueError:
                # Skip if time format is unexpected
                continue

            # 2. Categorize the event
            category_found = False
            for category, keywords in CATEGORY_KEYWORDS.items():
                if any(keyword.lower() in summary for keyword in keywords):
                    total_time_spent[category] += duration
                    category_found = True
                    break
            
            if not category_found:
                total_time_spent['Other'] += duration

        # 3. Aggregate and convert results to hours (float)
        stats_in_hours = {
            category: duration.total_seconds() / 3600 
            for category, duration in total_time_spent.items()
        }

        return stats_in_hours
    

# Example usage (for testing)
if __name__ == "__main__":
    manager = CalendarManager()
    
    # now_utc = datetime.now(timezone.utc).isoformat()
    # now_utc = now_utc[:-6]+'Z'
    # week_from_now_utc = (datetime.now(timezone.utc) + dt.timedelta(days=7)).isoformat()
    # week_from_now_utc = week_from_now_utc[:-6] +'Z'
    print(manager.get_timezone())

#     # print(f"{now_utc} to {week_from_now_utc}")
#      print("New\n New\n New")
#     # print(manager.print_all_events())
#     # event_info = manager.get_info("Breakfast event")
#     # event_id = event_info["id"]
#     # calendar_id = 'primary'
#     # manager.delete_event(event_id=event_id,calendar_id= calendar_id ,one_time= False)   
#     # print(manager.calculate_weekly_stats(now_utc, week_from_now_utc,"posaldis99@gmail.com"))
#     # manager.print_all_events()
#     # print(manager.print_all_events())
#     
# 
# 
# 
# 
# event_body= {
#     'summary': 'Team Sync-up Meeting',
#     'location': 'Conference Room A',
    
#     # Start and end times are critical and must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) 
#     # and include the timezone offset (e.g., -06:00 for CST).
#     'start': {
#         'dateTime': '2025-12-05T10:30:00-06:00',
#         'timeZone': 'America/Chicago',
#     },
#     'end': {
#         'dateTime': '2025-12-05T11:00:00-06:00',
#         'timeZone': 'America/Chicago',
#     },
    
#     # This is the 'description' key where your custom tags and notes go.
#     'description': 'Discuss Q4 roadmap and client deliverables.\n\nCustom Tags: #Roadmap #ProjectA #Internal',
    
#     # Optional: You can include a list of attendees
#     'attendees': [
#         {'email': 'user@example.com'},
#         {'email': 'teamlead@example.com', 'responseStatus': 'accepted'},
#     ],
    
#     # Optional: Reminders for the event
#     'reminders': {
#         'useDefault': False,
#         'overrides': [
#             {'method': 'email', 'minutes': 30},
#             {'method': 'popup', 'minutes': 10},
#         ],
#     },
# }
