from datetime import datetime, timedelta
import pytz
from googleapiclient.errors import HttpError

# --- Configuration for Event Categorization ---
# NOTE: Customize these lists based on common event titles in your calendar.
CATEGORY_KEYWORDS = {
    'Sleep': ['Sleep', 'Nap', 'Rest', 'Asleep'],
    'Work': ['Work', 'Meeting', 'Client', 'Project', 'Sprint', 'Standup'],
    'Leisure': ['Gym', 'Workout', 'Hobby', 'Reading', 'Movie', 'Personal Project', 'Run'],
    # Any event not matching the above will fall into the 'Other' category.
}


def calculate_weekly_stats(calendar_service, start_date_iso, end_date_iso, calendar_id='primary'):
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
    total_time_spent = {cat: timedelta(0) for cat in CATEGORY_KEYWORDS}
    total_time_spent['Other'] = timedelta(0)
    
    try:
        # gets the event list
        events_result = calendar_service.events().list(
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

# --- Example of function call preparation ---

def get_weekly_time_range():
    # Example: Calculate a range for the current calendar week (Sunday to Saturday)
    today = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate start of the week (assuming Sunday as start of the week)
    start_of_week = today - timedelta(days=today.weekday() + 1)
    end_of_week = start_of_week + timedelta(days=7)
    
    return start_of_week.isoformat(), end_of_week.isoformat()

