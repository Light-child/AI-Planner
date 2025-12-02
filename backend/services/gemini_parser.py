#Purpose: This module is responsible for all interactions with the Gemini AI API. 
# Its primary job is to take raw, natural language text input from the user and convert it into structured data
# (like a JSON object) that describes a calendar event.
import os
import json
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import google.generativeai as genai
import datetime as dt
import pytz


#Key Functionality:
class GeminiParser:
    #Loading the Gemini API key from .env.
    def __init__(self):
        #look for .env file and load its variables
        load_dotenv()
        #retrieve API key
        api_key = os.getenv("GEMINI_API_KEY")
        #if API key not found
        if not api_key:
            raise ValueError("\"GEMINI_API_KEY\" is not found in .env file")
        #present the API key to the google library to validate and allow you to usethe library
        genai.configure(api_key=api_key)
        #Initializing the GEmini model.
        self.model= genai.GenerativeModel('gemini-2.0-flash')
    
    def parse_event_details(self,user_input):
        """This is the pace for your logic for interacting with the AI model
         returns the json string """
        now = dt.datetime.now()
        current_date_str = now.strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""
        **Role:** You are a Time Format Converter and Event Structuring Assistant.
        **Goal:** Your sole task is to take the user's input describing a task, event, and its time, and convert it into the precise output format: "**[Event Name] on [Day of Week]: [Start Time] - [End Time] ([Duration])**".
        **Constraints & Rules:**
1.  **Extract the Event Name:** Identify the core activity or event.
2.  **Determine Day and Time:** Accurately extract the day, start time, and end time.
3.  **Calculate Duration:** Calculate the difference between the start and end time and express it in hours or minutes (e.g., '2 hours' or '30 minutes').
4.  **Strict Output Format:** The final output **MUST** strictly adhere to this format: `[Event Name] on [Day of Week]: [Start Time] - [End Time] ([Duration])`. Use 12-hour clock (AM/PM).

**Example Input and Output:**

**User Input:** "I have to work out in the morning, starting Tuesday at 7:30 and finishing at 8:30."
**Your Output:** "Work out on Tuesday: 7:30 AM - 8:30 AM (1 hour)"
**User Input:** "{user_input}"
"""
        try:
            response = self.model.generate_content(prompt).text
            #response should bee a json file
            # cleaned_response_text = response.text.strip("` \n")
            # cleaned_response_text = cleaned_response_text.replace("json\n", "", 1)
            return response
        except Exception as e:
            return f"Error interacting wih Gemini. Error: {e}"
        
    def avaiable_models(self):
        print("List of avilable models")
        lst = []
        try:
            for model in genai.list_models():
                # Checking if model supports 'generateContent'
                if 'generateContent' in model.supported_generation_methods:
                    #model.name returns "models/{model_name}"
                    #We woul remove the "models/"
                    model_id = model.name.split('/')[-1]
                    lst.append(model_id)
                    print(f"-{model.name} (Supports generateContent)")
            return lst
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
        
    def suggest_time(self, user_prompt, free_busy_data):
        """
        Generates scheduling suggestions based on user input and calendar availability.
        """
        # Convert the free_busy_data into a string that's easy for the AI to understand.
        busy_slots_str = "I am busy during these times (UTC): "
        if free_busy_data and free_busy_data['busy']:
            for slot in free_busy_data['busy']:
                busy_slots_str += f"from {slot['start']} to {slot['end']}. "
        else:
            busy_slots_str += "I have no known busy times."

        # Craft the new prompt for Gemini.
        prompt = (
            f"The user wants to schedule an event. User request: '{user_prompt}'. "
            f"Here are my current busy times: {busy_slots_str} "
            "Please suggest 3 available times for the user's event."
            "The format of your response should be something like : 'a. Have the cotton event at 8:00am this friday  this \n"
            "'b. Have the cotton event at 5:00pm on Tuesday 26th August, 2025 \n c.Heve cotton event at noon tommorow'" \
            "There should be no other information given except from the suggestions in the format above"
            
        )

        try:
            response = self.model.generate_content(prompt)
            # Assuming the response is a JSON string, you'll need to parse it.
            # Use a library like 'json' or 'json5' for robust parsing.
            return response.text
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return None
        
    def suggest_recurring_event(self, user_prompt, free_busy_data):
         # Convert the free_busy_data into a string that's easy for the AI to understand.
        busy_slots_str = "I am busy during these times (UTC): "
        if free_busy_data and free_busy_data['busy']:
            for slot in free_busy_data['busy']:
                busy_slots_str += f"from {slot['start']} to {slot['end']}. "
        else:
            busy_slots_str += "I have no known busy times."

        
#         # Craft the new prompt for Gemini.
        prompt = (
            f"The user wants to schedule a recurring  event. User request: '{user_prompt}'. "
            f"Here are my current busy times: {busy_slots_str} "
        
            "All times in the user's input are in UTC. Please convert all timestamps to Central Daylight Time (CDT), which is UTC-5"
            "Look for times in the users week to place this event"
            "Please suggest  available times for the user's event."
            "Suggested  times must match perfectly with the user's busy times"
            "Try to make the number of hours as close as possible to that which is specified" 
            "To create a feasible schedule, consider breaking the hours into smaller, more manageable chunks across multiple days."
            "chunks can be as shoert as 15 mins and can be as long as 7 hours"
            "The format of your response should be this: [Event Name] Every [Day of Week]: [Start Time] - [End Time] ([Duration])"
            "The times, dates and can be changed but the form of the sentences should be the same: "
            """
            For example
            **
            Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)
            Gaming event Every Wednesday: 8:00 PM - 10:00 PM (2 hours)
            Gaming event Every Friday: 8:00 PM - 10:00 PM (2 hours)


            **Option 2: Weekend Focus**

            This concentrates the gaming time on the weekend, sacrificing weekday flexibility.

            Gaming event Every Saturday: 10:00 AM - 4:00 PM (6 hours)
            Gaming event Every Sunday: 10:00 AM - 2:00 PM (4 hours)"
            Do not give any extra information 
            """            
        )
        # prompt = f"""Here are the user's current busy times: {busy_slots_str}.All times in the user's input are in UTC. 
        # Please convert all timestamps to Central Daylight Time (CDT) 
        # , which is UTC-5". 
        # return the users busy times in natural language """
        try:
            response = self.model.generate_content(prompt)
            # Assuming the response is a JSON string, you'll need to parse it.
            # Use a library like 'json' or 'json5' for robust parsing.
            return response.text
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return None

    def parse_event_details_1(self, user_input: str) -> list[dict]:
        """
        Parses a structured event string and converts it into a list of
        dictionaries suitable for Google Calendar API.

        Args:
            user_input (str): The structured string containing event details,
                            e.g., "Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)".

        Returns:
            list[dict]: A list of dictionaries formatted for Google Calendar API.
        """
        events = []
        
        day_to_rrule = {
            "Monday": "MO", "Tuesday": "TU", "Wednesday": "WE",
            "Thursday": "TH", "Friday": "FR", "Saturday": "SA",
            "Sunday": "SU"
        }

        rrule_until = "20251231T235959Z"

        lines = user_input.strip().split('\n')

        pattern = re.compile(
            r"^(.*)Every (\w+):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M).*$",
            re.IGNORECASE
        )

        # Use America/Chicago timezone
        tz =pytz.timezone('America/Chicago')

        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = pattern.match(line)
            if not match:
                continue
            
            summary = match.group(1).strip()
            day_of_week_str = match.group(2).capitalize()
            start_time_str = match.group(3).strip()
            end_time_str = match.group(4).strip()
            
            rrule_day = day_to_rrule.get(day_of_week_str)
            if not rrule_day:
                print(f"Warning: Unrecognized day '{day_of_week_str}'")
                continue
            
            # Get current time in Chicago timezone
            now = datetime.now(tz)
            
            # Calculate next occurrence of the target day
            today_weekday = now.weekday()
            target_weekday = list(day_to_rrule.keys()).index(day_of_week_str)
            days_until_next = (target_weekday - today_weekday) % 7
            
            if days_until_next == 0:
                days_until_next = 7
                
            next_occurrence = now.date() + timedelta(days=days_until_next)

            try:
                start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
                end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()
            except ValueError as e:
                print(f"Error parsing time: {e}")
                continue
            
            # Create datetime objects with Chicago timezone
            start_datetime = datetime.combine(next_occurrence, start_time_obj, tzinfo=tz)
            end_datetime = datetime.combine(next_occurrence, end_time_obj, tzinfo=tz)
            
            # Format in RFC3339 format (required by Google Calendar)
            # Format: 2025-12-08T20:00:00-06:00
            iso_start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
            iso_end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
            
            # Add colon to timezone offset (Python doesn't include it by default)
            # Convert -0600 to -06:00
            iso_start_time = iso_start_time[:-2] + ':' + iso_start_time[-2:]
            iso_end_time = iso_end_time[:-2] + ':' + iso_end_time[-2:]
            
            recurrence_rule = f"RRULE:FREQ=WEEKLY;BYDAY={rrule_day};UNTIL={rrule_until}"
            
            event_dict = {
                "summary": summary,
                "description": f"{summary} on {day_of_week_str}",
                "start": {
                    "dateTime": iso_start_time,
                    "timeZone": "America/Chicago"
                },
                "end": {
                    "dateTime": iso_end_time,
                    "timeZone": "America/Chicago"
                },
                "recurrence": [recurrence_rule]
            }
            
            # Debug print to verify format
            print(f"Event: {summary}")
            print(f"Start: {iso_start_time}")
            print(f"End: {iso_end_time}")
            print("---")
            
            events.append(event_dict)

        return events
    def parse_recurring_event_line(self,user_input):
        """
        Parses a structured event string and converts it into a list of
        dictionaries suitable for Google Calendar API.

        Args:
            user_input (str): The structured string containing event details,
                            e.g., "Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)".

        Returns:
            list[dict]: A list of dictionaries formatted for Google Calendar API.
        """
        events = []
        
        day_to_rrule = {
            "Monday": "MO", "Tuesday": "TU", "Wednesday": "WE",
            "Thursday": "TH", "Friday": "FR", "Saturday": "SA",
            "Sunday": "SU"
        }

        rrule_until = "20251231T235959Z"

        line = user_input.strip()
        pattern = re.compile(
            r"^(.*)Every (\w+):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M).*$",
            re.IGNORECASE
        )
        # Use America/Chicago timezone
        tz =pytz.timezone('America/Chicago')
        
        line = line.strip()
        match = pattern.match(line)

        summary = match.group(1).strip()
        day_of_week_str = match.group(2).capitalize()
        start_time_str = match.group(3).strip()
        end_time_str = match.group(4).strip()

        rrule_day = day_to_rrule.get(day_of_week_str)
        if not rrule_day:
            print(f"Warning: Unrecognized day '{day_of_week_str}'")
            return
        
        # Get current time in Chicago timezone
        now = datetime.now(tz)
        
        # Calculate next occurrence of the target day
        today_weekday = now.weekday()
        target_weekday = list(day_to_rrule.keys()).index(day_of_week_str)
        days_until_next = (target_weekday - today_weekday) % 7
        
        if days_until_next == 0:
            days_until_next = 7
            
        next_occurrence = now.date() + timedelta(days=days_until_next)

        try:
            start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
            end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()
        except ValueError as e:
            print(f"Error parsing time: {e}")
            return
        
        # Create datetime objects with Chicago timezone
        start_datetime = datetime.combine(next_occurrence, start_time_obj, tzinfo=tz)
        end_datetime = datetime.combine(next_occurrence, end_time_obj, tzinfo=tz)
        
        # Format in RFC3339 format (required by Google Calendar)
        # Format: 2025-12-08T20:00:00-06:00
        iso_start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
        iso_end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
        
        # Add colon to timezone offset (Python doesn't include it by default)
        # Convert -0600 to -06:00
        iso_start_time = iso_start_time[:-2] + ':' + iso_start_time[-2:]
        iso_end_time = iso_end_time[:-2] + ':' + iso_end_time[-2:]
        
        recurrence_rule = f"RRULE:FREQ=WEEKLY;BYDAY={rrule_day};UNTIL={rrule_until}"
        
        event_dict = {
            "summary": summary,
            "description": f"{summary} on {day_of_week_str}",
            "start": {
                "dateTime": iso_start_time,
                "timeZone": "America/Chicago"
            },
            "end": {
                "dateTime": iso_end_time,
                "timeZone": "America/Chicago"
            },
            "recurrence": [recurrence_rule]
        }
    def parse_event_line(self, user_input):
        """
        Parses a structured event string and converts it into a list of
        dictionaries suitable for Google Calendar API.

        Args:
            user_input (str): The structured string containing event details,
                              e.g., "Gaming event on Monday: 8:00 PM - 10:00 PM (2 hours)".

        Returns:
            list[dict]: A list of dictionaries formatted for Google Calendar API,
                        or an empty list if parsing fails.
        """
        events = []
        
        day_to_rrule = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, 
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }

        # New pattern to match "Summary on Day: Start - End (Duration)"
        # Note the change from 'Every' to 'on' and the addition of optional duration at the end
        pattern = re.compile(
            r"^(.*)on (\w+):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)\s*(\(.*\))?$",
            re.IGNORECASE
        )
        # Use America/Chicago timezone
        tz = pytz.timezone('America/Chicago')
        
        line = user_input.strip()
        match = pattern.match(line)
        
        if not match:
            print(f"Error: Input string format not recognized: {user_input}")
            return []

        summary = match.group(1).strip()
        day_of_week_str = match.group(2).capitalize()
        start_time_str = match.group(3).strip()
        end_time_str = match.group(4).strip()
        # duration_str = match.group(5) # Captured but not used, as duration is implicit

        target_weekday_index = day_to_rrule.get(day_of_week_str)
        if target_weekday_index is None:
            print(f"Warning: Unrecognized day '{day_of_week_str}'")
            return []
        
        # Get current time in Chicago timezone
        now = datetime.now(tz)
        
        # Calculate the next occurrence of the target day.
        # This makes it a single, non-recurring event on the next specified day.
        today_weekday_index = now.weekday() # Monday is 0, Sunday is 6
        days_until_next = (target_weekday_index - today_weekday_index) % 7
        
        # If it's today, set the date for today, otherwise, set for the next day.
        # Original code enforced the *next* week if it was today, but for a single
        # event 'on Monday' it's usually meant to be the current week's Monday 
        # unless the time has already passed. For simplicity, we choose the next one.
        if days_until_next == 0:
             # Check if the time has already passed on the current day
            try:
                start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
            except ValueError as e:
                print(f"Error parsing start time: {e}")
                return []
            
            # Combine current date with start time
            today_start_datetime = datetime.combine(now.date(), start_time_obj, tzinfo=tz)
            
            if now > today_start_datetime:
                # Time has passed, schedule for next week
                days_until_next = 7
            else:
                # Time has not passed, schedule for today
                days_until_next = 0
            
        next_occurrence = now.date() + timedelta(days=days_until_next)

        try:
            start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
            end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()
        except ValueError as e:
            print(f"Error parsing time: {e}")
            return []
        
        ## Create naive datetime objects first
        start_naive = datetime.combine(next_occurrence, start_time_obj)
        end_naive = datetime.combine(next_occurrence, end_time_obj)

        # Localize the naive datetime objects using pytz to get the correct offset (e.g., -06:00)
        # 'tz' is your pytz.timezone('America/Chicago') object
        start_datetime = tz.localize(start_naive)
        end_datetime = tz.localize(end_naive)

        # Handle case where end time is on the next day (e.g., 10 PM - 2 AM)
        if end_time_obj < start_time_obj:
            end_datetime += timedelta(days=1)

        # Format in RFC3339 format using the correct format string
        # This uses the same method as before to insert the colon
        iso_start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
        iso_end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Add colon to timezone offset (Python doesn't include it by default)
        iso_start_time = iso_start_time[:-2] + ':' + iso_start_time[-2:]
        iso_end_time = iso_end_time[:-2] + ':' + iso_end_time[-2:]
        
        # Removed recurrence rule as the string "on Monday" suggests a single event
        # If recurrence is needed, the pattern and logic for date calculation 
        # should be reverted/re-added.
        
        event_dict = {
            "summary": summary,
            "description": f"{summary} on {day_of_week_str}",
            "start": {
                "dateTime": iso_start_time,
                "timeZone": "America/Chicago"
            },
            "end": {
                "dateTime": iso_end_time,
                "timeZone": "America/Chicago"
            }
            # 'recurrence' key is removed for a single event
        }
        
    
        return event_dict

#Alternativ

# Example Usage:
# This demonstrates how the function would process your input.

if __name__ == "__main__":
    gem = GeminiParser()
#     test_string = """
# Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)
# Gaming event Every Tuesday: 8:00 PM - 10:00 PM (2 hours)
# Gaming event Every Wednesday: 8:00 PM - 10:00 PM (2 hours)
# Gaming event Every Thursday: 8:00 PM - 10:00 PM (2 hours)
# Gaming event Every Friday: 8:00 PM - 10:00 PM (2 hours)
# """
    
#     parsed_events =gem.parse_event_details(test_string)
    
#     # Print the resulting list of dictionaries, formatted nicely.
    
#     # print(json.dumps(parsed_events, indent=2))
#     print(parsed_events)

    print(gem.suggest_recurring_event("I want to spend 4 hours a week making lemonade. My Tuesdays and Thursdays are free enough."))





#Defining the prompt that instructs Gemini on what information to extract (summary, description, start time, end time, etc.) and in what format (e.g., JSON).
#Sending the user's text input to the Gemini API.
#Parsing Gemini's response to extract the structured event data.
#Handling potential errors or ambiguities from the AI's response.
#Connection: main.py will call functions within this module to process user input.

