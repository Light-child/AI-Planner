#Purpose: This is the central control script of your command-line interface (CLI) application.
# It orchestrates the flow, tying together the gemini_parser.py and calendar_manager.py modules.
#Key Functionality:

    #Initializes the application (e.g., loads environment variables).
    #Presents a command-line interface to the user, allowing them to type in requests.
    #Takes the user's natural language input.
    #Passes this input to gemini_parser.py to extract event details.
    #Performs any necessary validation or default-setting on the data received from the parser.
    #Passes the validated event details to calendar_manager.py to create the event.
    #Provides feedback to the user based on the success or failure of the operations (including structured error messages).
    #Manages the main application loop (e.g., continues to ask for input until the user types 'exit').

#Connection: This file imports and uses functions from both gemini_parser.py and calendar_manager.py. It's the "brain" that coordinates the other specialized modules

import json
import datetime as dt
from datetime import timezone, timedelta
from datetime import datetime
from services.gemini_parser import GeminiParser
from services.calender_manager import CalendarManager
import statistics

def create_event(user_input, gemini_parser, calender_manager):
    #Pass the user input to Gemini
    gemini_response_text = gemini_parser.parse_event_details(user_input)
    
    # Parse the JSON output from gemini
    try:
        parsed_data = json.loads(gemini_response_text)
        print("\nGemini successfully parsed the event details: ")
        print(parsed_data)

    except json.JSONDecodeError:
        print("Error: Gemini's response was not valid")
        print("Raw response:",gemini_response_text)
        return
     
    #Check if this is an availability checks or an event to create.
    if parsed_data.get("request_type") == "availability_check":
        print("\nThis is a request for availability. The functionality is not yet implemented.")
        #You'll build this part later
        return 
    
    # Format the data for the Google Calender API
    # The Google Calender API expects time in ISO 8601 format.    # The JSON from Gemini needs to be converted
    try:
        # Example conversion (assuming Gemini returns "YYYY-MM-DD HH:MM:SS" format)
        # You may need to adjust the format based on your prompt engineering.
        start_time_str = parsed_data.get("start_time")
        end_time_str = parsed_data.get("end_time")

        # Strip the timezone offset from the string
        # This takes a string like "2025-08-16T12:00:00-00:00" and makes it "2025-08-16T12:00:00"
        if start_time_str and len(start_time_str) > 19:
            start_time_str = start_time_str[:-6]
        if end_time_str and len(end_time_str) > 19:
            end_time_str = end_time_str[:-6]

        start_datetime = datetime.datetime.fromisoformat(start_time_str)
        end_datetime = datetime.datetime.fromisoformat(end_time_str)

        # Create the event body in the format the Google Calender API
        event_body = {
            'summary': parsed_data.get('summary'),
            'description': parsed_data.get('description'),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Chicago',  # Or your local timezone
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Chicago',
            },
            
        }

        # Conditionally add the recurrence field
        recurrence_rule = parsed_data.get('recurrence')
        if recurrence_rule:
            event_body['recurrence'] = [recurrence_rule]
            print("\nRecurring event detected. Adding recurrence rule to event body.")

        # Pass the event data to the Calender Manger
        print("\nAttempting to create event...")
        created_event = calender_manager.add_event(event_body)

        if created_event:
            print("\n Event Created succesfully!")
            print(f"Event ID: {created_event['id']}")
            print(f"Event URL: {created_event["htmlLink"]}")
    except(KeyError, ValueError) as e:
        print(f"Error: Missing or invalid data for event creation: {e}")
        print("Please ensure Gemini's output contains valid 'summary', 'description', 'start_time', and 'end_time' keys.")

def plan_event(user_input, gemini_parser, calender_manager):
    # 1. First, check if the user wants to *find* a time or *create* an event.
    #    You'll need a simple classifier for this. For now, let's assume if
    #    the prompt contains keywords like "find a time," "schedule for me,"
    #    or "when am I free," we trigger the suggestion workflow.
    
    if True:
        print("Finding available times...")
        
        # 2. Get free/busy data from the CalendarManager.
        #    You'll need to decide the date range to check (e.g., next 7 days).
        #    Let's assume get_free_busy_slots takes a start and end date.
        
        # This is a placeholder; you'll need to implement this logic.
        now = datetime.now(timezone.utc)
        start_date = now.strftime("""%Y-%m-%dT%H:%M:%SZ""")

        days_to_add = 10

        end = now + timedelta(days= days_to_add)
        
        end_date = end.strftime("%Y-%m-%dT%H:%M:%SZ")
        free_busy_data = calender_manager.get_free_busy_slots(start_date, end_date)
        
        # 3. Call the new GeminiParser method.
        suggestions_str = gemini_parser.suggest_time(user_input, free_busy_data)
        
        if suggestions_str:
            # suggestions_data = json.loads(suggestions_json_str)
            print("Here are some suggested times:")
            return suggestions_str
            # for suggestion in suggestions_data.get('suggestions', []):
            #     print(f"- {suggestion}")
        else:
            print("Could not generate suggestions. Please try again.")

def plan_recurring_event(user_input, gemini_parser, calender_manager):
    print("Finding available times...")
    if True:
        # 2. Get free/busy data from the CalendarManager.
        #    You'll need to decide the date range to check (e.g., next 7 days).
        #    Let's assume get_free_busy_slots takes a start and end date.
        
        # This is a placeholder; you'll need to implement this logic.
        
        now_utc = datetime.now(timezone.utc).isoformat()
        now_utc = now_utc[:-6]+'Z'

        week_from_now_utc = (datetime.now(timezone.utc) + dt.timedelta(days=30)).isoformat()
        week_from_now_utc = week_from_now_utc[:-6] +'Z'


        free_busy_data = calender_manager.get_free_busy_slots(now_utc, week_from_now_utc)
        
        # 3. Call the new GeminiParser method.
        suggestions_str = gemini_parser.suggest_recurring_event(user_input, free_busy_data)
        
        if suggestions_str:
            # suggestions_data = json.loads(suggestions_json_str)
            print("Here are some suggested times:")
            return suggestions_str
            # for suggestion in suggestions_data.get('suggestions', []):
            #     print(f"- {suggestion}")
        else:
            print("Could not generate suggestions. Please try again.")

def main():

    #get info from user about morning r day person. Do they want a day off without work. do they want to work at a stretch.  Do they want to break up

    # get user to add specifics like: I want to have 15 mins sessions

    print("Welcome to the AI Calender Scheduler!")

    cal = CalendarManager()
    gem = GeminiParser()
    
    inpt = input()
    # a = plan_event(inpt, gem, cal)
    # print("=" * 10)
    # print(a)
    # inpt = gem.parse_event_details(inpt)
    
    now_utc = datetime.now(timezone.utc).isoformat()
    now_utc = now_utc[:-6]+'Z'
    week_from_now_utc = (datetime.now(timezone.utc) + dt.timedelta(days=7)).isoformat()
    week_from_now_utc = week_from_now_utc[:-6] +'Z'

    free = cal.get_free_busy_slots(now_utc, week_from_now_utc)

    print(gem.suggest_recurring_event("I want to spend 4 hours a week making lemonade. My Tuesdays and Thursdays are free enough.", free))




     
    


if __name__ == "__main__":
    main()
        


