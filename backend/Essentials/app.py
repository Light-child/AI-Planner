from flask import Flask, request, jsonify
from services.calender_manager import CalendarManager
from services.gemini_parser import GeminiParser
from datetime import timezone, timedelta
from datetime import datetime
from flask_cors import CORS

cal = CalendarManager()
gem = GeminiParser()


app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Test if API is working"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Scheduler API is running!',
        'timestamp': datetime.now().isoformat()
    })

@app.route("/signup")
def signup():
    cal.get_calendar_service()
    print("Success")

@app.route("/create_event", methods= ['POST'])
def create_event():
    data = request.get_json()
    det = gem.parse_event_details(data["input"])
    return cal.add_event(det)

@app.route("/create_event_nlp", methods = ["POST"])
def create_event_nlp():
    """        Args:
            user_input (str): The structured string containing event details,
                            e.g., "Gaming event Every Monday: 8:00 PM - 10:00 PM (2 hours)"."""
    try:
        data = request.get_json()
        # user_input = request.data.decode("utf-8")
        #Or user_input = request.get_data(as_text=True)
        user_input = gem.parse_event_details(data["input"])
        event_details = gem.parse_event_line(user_input)
        cal.add_event(event_details)
        return jsonify({
            'status': 'success',
            'message': 'Event created successfully',
            'input': user_input,
            'event_details': event_details
        }), 201
        
    except Exception as e:
        return str(e)
    
@app.route("/delete_event", methods = ['POST'])
def delete_event():
    data  = request.get_json()
    try:
        cal.delete_event(data["id"], data["calendar_id"], True)
        return "True"
    except Exception as e:
        return f"{e}"

@app.route("/plan_event", methods =["POST"] )
def plan_single_event():
    """
    Expecting JSON file that has the "input" key that maps to user input and
    "range" which is number of days

    Returns strings
    """
    print("Finding available times...")
    data = request.get_json()
    user_input = data["input"]
    days_to_add = int(data["range"])
    
    # 2. Get free/busy data from the CalendarManager.
    #    You'll need to decide the date range to check (e.g., next 7 days).
    #    Let's assume get_free_busy_slots takes a start and end date.
    
    # This is a placeholder; you'll need to implement this logic.
    now = datetime.now(timezone.utc)
    start_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    end = now + timedelta(days= days_to_add)
    
    end_date = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    free_busy_data = cal.get_free_busy_slots(start_date, end_date)
    
    # 3. Call the new GeminiParser method.
    suggestions_str = gem.suggest_time(user_input, free_busy_data)
    
    if suggestions_str:
        # suggestions_data = json.loads(suggestions_json_str)
        print("Here are some suggested times:")
        return suggestions_str
        # for suggestion in suggestions_data.get('suggestions', []):
        #     print(f"- {suggestion}")
    else:
        print("Could not generate suggestions. Please try again.")

@app.route("/plan_recurring_event", methods = ["POST"])
def plan_recurring_event():
    pass


app.run(host="0.0.0.0", port= 80)