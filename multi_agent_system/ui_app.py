import streamlit as st
import requests
import json
import logging # Added for better error logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Reading json for user specific variables
try:
    with open("./config.json", 'r') as f:
        config = json.load(f)
    api_url = config["backend_url"]
except FileNotFoundError:
    st.error("Error: config.json not found. Please ensure the configuration file exists.")
    st.stop() # Stop execution if config is missing


st.title("Doctor Appointment System")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Get User ID - consider placing it in a sidebar or making it less prominent after initial entry
# You might want to store the userid in session_state as well once entered.
userid_input = st.text_input("Please provide your User ID", key="user_id_input")

# Display existing chat messages
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# Handle new chat input
if query := st.chat_input("Please provide your query (e.g: 'Book an appointment for a certain date')"):
    # Check if User ID is provided
    if not userid_input:
        st.warning("Please provide your User ID before submitting the query.")
        st.stop() # Stop processing if no user ID

    # --- Add user's message to history and display it immediately ---
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(query)
    # --- ---

    # Convert userid to integer (assuming backend expects int)
    try:
        user_id_int = int(userid_input)
    except ValueError:
        st.error("Invalid User ID. Please enter a numeric ID.")
        # Remove the user message we just added optimistically
        st.session_state.messages.pop()
        st.stop()


    # Call the backend API
    try:
        # Show a thinking indicator
        with st.spinner("Thinking..."):
             response = requests.post(api_url, json={"query": query, "id_number": user_id_int}, timeout=30) # Added timeout
             response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        logging.info(f"Received response data: {response_data}") # Log the response

        # --- Process and display assistant's response ---
        if "messages" in response_data and isinstance(response_data["messages"], list):
            # Extract the last assistant message (assuming the API returns the full history or just the last reply)
            # Adjust this logic if your API returns multiple new messages
            assistant_messages = [msg for msg in response_data["messages"] if msg.get("type") == "ai" or msg.get("role") == "assistant"] # Handle different possible keys

            if assistant_messages:
                 # Get the last message content
                 last_assistant_message = assistant_messages[-1]
                 if 'content' in last_assistant_message:
                     assistant_content = last_assistant_message['content']
                     # Add assistant's response to history
                     st.session_state.messages.append({"role": "assistant", "content": assistant_content})
                     # Display assistant's response
                     with st.chat_message("assistant", avatar="🤖"):
                         st.write(assistant_content)
                 else:
                     st.warning("Received assistant message without 'content'.")
                     logging.warning("Assistant message missing 'content': %s", last_assistant_message)
            else:
                 st.warning("No assistant messages found in the response.")
                 logging.warning("No assistant messages in response: %s", response_data)

        else:
            st.error("Received an unexpected response format from the API.")
            logging.error("Unexpected API response format: %s", response_data)
        # --- ---

    except requests.exceptions.RequestException as e:
        st.error(f"Network error: Could not connect to the API. {e}")
        logging.error(f"API connection error: {e}")
        # Remove the user message we added optimistically if the API call fails
        st.session_state.messages.pop()
    except json.JSONDecodeError:
        st.error("Error: Could not decode the API response.")
        logging.error(f"API JSON decode error. Status: {response.status_code}, Body: {response.text}")
        st.session_state.messages.pop()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        logging.exception("Unexpected error in chat input processing:") # Log the full traceback
        # Remove the user message we added optimistically
        if st.session_state.messages[-1]["role"] == "user": # Basic check before popping
             st.session_state.messages.pop()
        # Rerun to clear the spinner and show the error correctly
        st.rerun()


# Optional: Add a way to clear history for testing
# if st.button("Clear History"):
#     st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]
#     st.rerun()

            





# if st.button("Submit"):
#     if not userid and not query:
#         st.warning("Please provide the valid details")
#     try:
        
#         response = requests.post(api_url, json={"query": query, "id_number":userid})
#         if response.status_code == 200:
#             st.success("Received Reponse")
#             output = [message['content'] for message in response.json()["messages"]]
#             st.write(output)
            
#         else:
#             st.error(f"Request failed with status code: {response.status_code}")
#     except Exception as e:
#         st.error(f"An error occurred: {e}")
        
    





