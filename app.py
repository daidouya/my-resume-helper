import streamlit as st
import uuid
import requests
import base64

BACKEND_URL = "http://localhost:8000"

#### Session State Initialization
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_ready" not in st.session_state:
    st.session_state.chat_ready = False
if "resume_processed" not in st.session_state:
    st.session_state.resume_processed = False
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "response_pending" not in st.session_state:
    st.session_state.response_pending = False

#### Helpers
def encode_file(file):
    file_bytes = file.getvalue()
    return base64.b64encode(file_bytes).decode("utf-8")

def stream_from_backend(prompt, user_id):
    response = requests.post(
        BACKEND_URL + "/chat",
        json={"input": prompt, "user_id": user_id},
        stream=True,
    )
    for chunk in response.iter_content(chunk_size=1):
        if chunk:
            yield chunk.decode("utf-8")

st.title("📄 Resume Parser + Chatbot")

uploaded_file = st.file_uploader("Choose your resume", type=["pdf"])

# Detect if a new file is uploaded
if uploaded_file:
    if uploaded_file.name != st.session_state.last_uploaded_file:
        st.session_state.resume_processed = False
        st.session_state.chat_ready = False
        st.session_state.messages = []
        st.session_state.last_uploaded_file = uploaded_file.name

### Upload + Parse Resume
if uploaded_file and not st.session_state.resume_processed:
    resume_str = encode_file(uploaded_file)

    with st.spinner("Uploading resume..."):
        upload_payload = {'user_id': st.session_state.user_id, 'file': resume_str}
        upload_response = requests.post(BACKEND_URL + '/upload', json=upload_payload)

    if upload_response.status_code == 200:
        with st.spinner("Parsing resume..."):
            parse_payload = {'user_id': st.session_state.user_id}
            parse_response = requests.post(BACKEND_URL + "/parse", json=parse_payload)

        if parse_response.status_code == 200:
            st.success("✅ Resume uploaded and parsed!")
            st.session_state.resume_processed = True
        else:
            st.error("❌ Failed to parse resume.")
    else:
        st.error("❌ Failed to upload resume.")

if st.session_state.resume_processed and not st.session_state.chat_ready:
    if st.button("💬 Start Chat with Resume Assistant"):
        st.session_state.chat_ready = True

### Chat Interface
if st.session_state.chat_ready:

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.response_pending:
        prompt = st.chat_input("Ask a question about your resume...")

    if prompt:
        st.session_state.response_pending = True

        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Thinking...")

            try:
                reply = ""
                for chunk in stream_from_backend(prompt, st.session_state.user_id):
                    reply += chunk
                    placeholder.markdown(reply)
            except Exception as e:
                reply = f"Error: {e}"
                placeholder.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.response_pending = False 