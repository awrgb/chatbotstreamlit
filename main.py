import streamlit as st
import psycopg2
from openai import OpenAI

# Set up the OpenAI client for NVIDIA's API
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"  # Replace with your actual API key
)

# Define the connection string
conn_string = "postgresql://chatbot_owner:PJ8jmFDGZEL1@ep-spring-boat-a88jc75h.eastus2.azure.neon.tech/chatbot?sslmode=require"

# Connect to the PostgreSQL database
def get_db_connection():
    try:
        conn = psycopg2.connect(conn_string)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None  # Return None if connection fails

# Save chat messages to the database
def save_chat_to_db(user_message, ai_message):
    try:
        conn = get_db_connection()
        if conn is not None:  # Check if connection was successful
            cur = conn.cursor()
            cur.execute("INSERT INTO chat_history (user_message, ai_message) VALUES (%s, %s)", (user_message, ai_message))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        st.error(f"An error occurred while saving to the database: {e}")

# Delete chat history from the database
def delete_chat_from_db(user_message):
    try:
        conn = get_db_connection()
        if conn is not None:  # Check if connection was successful
            cur = conn.cursor()
            cur.execute("DELETE FROM chat_history WHERE user_message = %s", (user_message,))
            conn.commit()
            cur.close()
            conn.close()
    except Exception as e:
        st.error(f"An error occurred while deleting from the database: {e}")

# Fetch chat history from the database
def fetch_chat_history():
    try:
        conn = get_db_connection()
        if conn is not None:  # Check if connection was successful
            cur = conn.cursor()
            cur.execute("SELECT user_message, ai_message FROM chat_history ORDER BY timestamp ASC;")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows  # Return fetched rows
    except Exception as e:
        st.error(f"An error occurred while fetching chat history: {e}")
        return []

# Initialize chat history in session state if it does not exist
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = fetch_chat_history()  # Load chat history from DB

if st.sidebar.button("New Chat"):
    st.session_state["chat_history"] = []

# Model parameters in the sidebar
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
top_p = st.sidebar.slider("Top P", 0.0, 1.0, 0.9)
max_tokens = st.sidebar.slider("Max Tokens", 100, 2048, 1024)
stream_response = st.sidebar.checkbox("Stream Response", value=True)

# Main UI for the chatbot
st.markdown("<h1 style='text-align: center;'>Zoro GPT</h1>", unsafe_allow_html=True)
st.markdown("---")  # Add a line under the title for separation

# Set the background color and other styles for dark theme
st.markdown(
    """
  <style>
.stApp {
    background-color: #0e1117;
    color: white;
}

.chat-bubble {
    border-radius: 10px;
    padding: 10px;
    margin: 5px 0;
}

.user-bubble {
    background-color: #007BFF;  /* User message background color */
    color: white;  /* Text color */
    text-align: right;  /* Text aligned to the right */
    width: fit-content;  /* Width adjusts to content */
    max-width: 70%;  /* Maximum width */
    margin-left: auto;  /* Align to the right */
    margin-right: 10px;  /* Add some space from the right edge */
    padding: 10px;  /* Padding for better appearance */
    border-radius: 15px;  /* Rounded corners */
}

.ai-bubble {
    background-color: #343a40;  /* AI message background color */
    color: white;  /* Text color */
    text-align: left;  /* Text aligned to the left */
    width: fit-content;  /* Width adjusts to content */
    max-width: 70%;  /* Maximum width */
    margin-right: auto;  /* Align to the left */
    margin-left: 10px;  /* Add some space from the left edge */
    padding: 10px;  /* Padding for better appearance */
    border-radius: 15px;  /* Rounded corners */
}

/* Styling for the button */
button[data-baseweb="button"] {
    background-color: #28a745; /* Green color */
    color: white; /* Text color */
    border-radius: 10px; /* Rounded corners */
    padding: 10px 20px; /* Padding */
    font-size: 18px; /* Font size */
}

button[data-baseweb="button"]:hover {
    background-color: #218838; /* Darker green on hover */
}
</style>
    """,
    unsafe_allow_html=True
)

# Input box for the user's message
user_input = st.chat_input("Message ZoroGPT")  # Added key for state management

# Send message automatically on pressing Enter
if user_input:
    # Append user's message to the chat history
    st.session_state["chat_history"].append((user_input, ""))  # Append empty AI response for now

    # Call the NVIDIA API to generate a response
    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.2-3b-instruct",  # Replace with the correct model
            messages=[{"role": "user", "content": user_input}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=stream_response
        )

        # Stream response if enabled
        ai_response = ""
        if stream_response:
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
        else:
            ai_response = completion.choices[0].message["content"]

        # Append AI's response to chat history and save to DB
        st.session_state["chat_history"][-1] = (user_input, ai_response)
        save_chat_to_db(user_input, ai_response)

    except Exception as e:
        st.error(f"An error occurred while processing the response: {e}")

# Display chat messages
for user_msg, ai_msg in st.session_state["chat_history"]:
    st.write(f"<div class='chat-bubble user-bubble'>{user_msg}</div>", unsafe_allow_html=True)
    st.write(f"<div class='chat-bubble ai-bubble'>{ai_msg}</div>", unsafe_allow_html=True)
    st.write("---")

# Sidebar for Chat History
st.sidebar.header("Chat History")
for index, (user_msg, ai_msg) in enumerate(st.session_state["chat_history"]):
    with st.sidebar.expander(f"Chat: {user_msg[:20]}..."):  # Display first 20 chars for brevity
        st.write(f"**User:** {user_msg}")
        st.write(f"**AI:** {ai_msg}")

        # Delete option with a unique key
        if st.button("Delete", key=f"delete_{index}"):  # Using index for uniqueness
            st.session_state["chat_history"].remove((user_msg, ai_msg))
            delete_chat_from_db(user_msg)  # Call to delete from DB
            st.experimental_rerun()  # Rerun the app to refresh state

# Clear input box (this should be handled automatically by Streamlit with key)
if 'input_text' in st.session_state:
    st.session_state['input_text'] = ""
