import streamlit as st
import pandas as pd
import google.generativeai as genai

# -----------------------------
# Setup
# -----------------------------
st.title("🧠 AI Chatbot for CSV Understanding")
st.caption("Upload a CSV and ask anything about your data!")

# Load Gemini API key from secrets
gemini_api_key = st.secrets["gemini_api_key"]

# Initialize Gemini model
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini is ready.")
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")

# -----------------------------
# Session state setup
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "csv_data" not in st.session_state:
    st.session_state.csv_data = None
if "csv_summary" not in st.session_state:
    st.session_state.csv_summary = ""

# -----------------------------
# Upload CSV
# -----------------------------
st.subheader("📁 Upload Your CSV File")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.csv_data = df
        st.session_state.csv_summary = df.describe(include='all').fillna("").to_string()
        st.success("CSV uploaded successfully.")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Could not read file: {e}")

# -----------------------------
# Chat Interface
# -----------------------------
st.subheader("💬 Ask AI About Your Data")

if user_input := st.chat_input("Ask anything about your data..."):
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    if model and st.session_state.csv_data is not None:
        try:
            # Create a prompt that includes summary of the CSV
            prompt = f"""
You are a data analyst assistant. A user has uploaded a CSV file.
Here is a summary of the dataset:
{st.session_state.csv_summary}

Now the user asked:
{user_input}

Based on the dataset, answer in a clear and concise way.
"""
            response = model.generate_content(prompt)
            bot_reply = response.text

            # Display and store response
            st.chat_message("assistant").markdown(bot_reply)
            st.session_state.chat_history.append(("assistant", bot_reply))
        except Exception as e:
            st.error(f"Error generating response: {e}")

    elif model is None:
        st.warning("Gemini model not configured.")
    else:
        st.warning("Please upload a CSV file first.")

# -----------------------------
# Display past chat
# -----------------------------
for role, msg in st.session_state.chat_history:
    if role != "user":  # avoid showing twice
        st.chat_message(role).markdown(msg)
