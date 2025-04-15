import streamlit as st
import requests


api_url = 'http://localhost:8000/chat'


st.title("Doctor Appointment System")

userid =  st.text_input("Please provide your id")
query = st.text_input("Please provide your query")

if st.button("Submit"):
    if not userid and not query:
        st.warning("Please provide the valid details")
    try:
        
        response = requests.post(api_url, json={"query": query, "id_number":userid})
        if response.status_code == 200:
            st.success("Received Reponse")
            output = [message['content'] for message in response.json()["messages"]]
            st.write(output)
            
        else:
            st.error(f"Request failed with status code: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        
    





