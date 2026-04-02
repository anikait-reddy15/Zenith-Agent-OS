import streamlit as st
import requests

# Point to the FastAPI server running silently in the background of the container
API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Zenith Agent OS", layout="centered")

st.title("Zenith Agent OS ⚡")
st.markdown("Your Autonomous Multi-Agent Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Zenith to manage tasks, files, or memory..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Orchestrator is routing tasks..."):
            try:
                response = requests.post(API_URL, json={"prompt": prompt})
                response.raise_for_status()
                
                answer = response.json().get("response", "System Error: No response received.")
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to backend API: {str(e)}")