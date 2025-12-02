from pymongo import MongoClient
from datetime import datetime

# --- Setup Connection (Ensure your mongod server is running) ---
client = MongoClient("mongodb://localhost:27017/")
db = client['mydatabase']
my_collection = db['product_mappings']

# # --- Define Your Data Structure ---
# fruit_color_mapping = {
#     "category": "Fruits and Colors",
#     "item_names": ["Apple", "Banana", "Orange"],
#     "item_attributes": ["Red", "Yellow", "Orange"]
# }

# # --- Insert the Document ---
# try:
#     result = my_collection.insert_one(fruit_color_mapping)
#     print(f"Successfully inserted document with ID: {result.inserted_id}")

# except Exception as e:
#     print(f"An error occurred during insertion: {e}")

# finally:
#     client.close()


def save_sync_link(task_id: str, event_links: list) -> bool:
    """
    Saves a record linking a task to one or more calendar events.
    
    The 'event_links' argument is the list of lists structure you requested:
    [ ['event_id_1', 'calendar_id_1'], ['event_id_2', 'calendar_id_2'], ... ]
    
    In a real app, this function would use the MongoDB client to insert a document.
    """
    
    # 1. Prepare the document using the requested structure
    sync_document = {
        "task_id": task_id,
        "linked_events": event_links,
        "created_at": datetime.now() # Good practice to always timestamp data
    }
    
    # 2. Database Insertion Placeholder
    # Example: db.sync_links.insert_one(sync_document)
    result = my_collection.insert_one(sync_document)
    
    # print(f"[MONGO_SERVICE] Successfully prepared and (placeholder) saved sync link:")
    # print(f"  Task ID: {sync_document['task_id']}")
    # print(f"  Linked Events Count: {len(sync_document['linked_events'])}")
    # print(f"  Example Link: {sync_document['linked_events'][0] if sync_document['linked_events'] else 'None'}")
    
    # You would check the insertion result here (e.g., if insert_one.inserted_id)
    return result
def add_event_to_task_link(task_id: str, new_event_link: list) -> bool:
    if not task_id:
            return False
        
    # 1. Define the Query (find the document matching the task_id)
    query = {"task_id": task_id}
    
    # 2. Define the Update Operation
    update_operation = {
        "$push": {"linked_events": new_event_link},
        "$set": {"last_updated": datetime.now()}
    }

    result = my_collection.update_one(query, update_operation)  # Changed from db.sync_links
    if result.modified_count > 0:
        print(f"Successfully updated task {task_id}")
        return True
    else:
        print(f"No document found or modified for task {task_id}")
        return False

def remove_event_from_task_link(task_id: str, event_to_remove: list) -> bool:
    """
    Finds an existing document by task_id and REMOVES a specific 
    [event_id, calendar_id] pair from the 'linked_events' list using the MongoDB $pull operator.
    
    This function handles removing a single link (your "remove one particular event" request).
    The 'event_to_remove' argument must be the exact list: ['event_id', 'calendar_id']
    """
    
    query = {"task_id": task_id}
    update_operation = {
        "$pull": {"linked_events": event_to_remove},
        "$set": {"last_updated": datetime.now()}
    }
    
    # --------------------------------------------------------------------------
    # PRACTICAL CODE STEP: MongoDB Update using $pull
    # --------------------------------------------------------------------------

    result = my_collection.update_one(query, update_operation)
    # print(result)
    if result.modified_count > 0:
        # print("Success") 
        return True

    print(f"UNABLE to remove event from sync link for Task ID: {task_id}, removed {event_to_remove}")
    return False

def delete_task_id(task_id: str) -> bool:
    """
    Deletes the entire sync link document (the key-value pair) 
    matching the given task_id. (Your "delete key and value" request).
    """
    
    query = {"task_id": task_id}
    
    result = my_collection.delete_one(query)
    if result.deleted_count == 0:
        print(f"UNABLE TO  DELETE ENTIRE sync link document for Task ID: {task_id}")
        return False
    return True

def get_event_by_task_id(task_id: str):
    """
    Returns a 2D list of event_ids and calender ids using the task_id. 
    This is necessary for operations like checking existing links before deleting.
    """
    
    query = {"task_id": task_id}

    document = my_collection.find_one(query)
    if document:
        return document ['linked_events']
    
    
    print(f"[MONGO_SERVICE] Placeholder: No sync link found for Task ID: {task_id}")
    return None
# Assuming 'db' is your initialized PyMongo database instance
# and 'sync_links' is your collection name

def get_task_by_event_id(db_client, event_id: str):
    """
    Finds the task associated with a specific Google Calendar Event ID.

    This is necessary for the synchronization logic: when an event needs 
    to be deleted or modified based on an action taken on the corresponding task.

    Args:
        db_client: The PyMongo database client object.
        event_id: The Google Calendar Event ID string to search for.

    Returns:
        dict | None: The document containing the task_id, tasklist_id, 
                     and the list of event_ids, or None if not found.
    """
    try:
        # 1. Access the 'sync_links' collection
        sync_links_collection = db_client.sync_links
        
        # 2. Query: Find the document where the 'event_ids' array contains the target event_id.
        query = {
            "event_ids": event_id
        }
        
        # 3. Execute the query
        sync_link_document = sync_links_collection.find_one(query)
        
        if sync_link_document:
            print(f"DEBUG: Found sync link for event ID {event_id}.")
            
            # The document includes the _id field which contains the task_id and tasklist_id
            return sync_link_document
        else:
            print(f"DEBUG: No sync link found for event ID {event_id}.")
            return None

    except Exception as e:
        print(f"ERROR in get_task_by_event_id: {e}")
        return None


if __name__ == "__main__":
    #---------------------------------------------------------------------
    # WORKS !!!!
    print(save_sync_link("Test task_id",[["test event_id", "test cal_id"]]))
    # print(add_event_to_task_link("Test task_id",["test1 event_id", "test1 cal_id"] ))
    # remove_event_from_task_link("Test task_id", ["test1 event_id", "test1 cal_id"])
    # print(get_event_by_task_id("Test task_id"))
    # delete_task_id("Test task_id")
    #---------------------------------------------------------------------------------
    
    

 