import streamlit as st
import pandas as pd
import google.generativeai as genai
import textwrap

# === CONFIG ===
st.set_page_config(page_title="Gemini CSV Analyst", layout="wide")
st.title("📊 CSV + Gemini: Ask Anything About Your Data")
st.caption("Upload a dataset, ask questions in natural language, and get real answers.")

# === API SETUP ===
try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
    
    def role_to_streamlit(role):
        return "assistant" if role == "model" else role

except Exception as e:
    st.error(f"❌ Error initializing Gemini: {e}")
    st.stop()

# === SESSION ===
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dictionary" not in st.session_state:
    st.session_state.dictionary = None

# === UPLOAD ===
st.subheader("📥 Upload Your Dataset and Dictionary")
data_file = st.file_uploader("Upload CSV Data", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary (CSV or TXT)", type=["csv", "txt"])

if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")

if dict_file:
    try:
        if dict_file.name.endswith(".csv"):
            dict_df = pd.read_csv(dict_file)
            dict_text = dict_df.to_string(index=False)
        else:
            dict_text = dict_file.read().decode("utf-8")
        st.session_state.dictionary = dict_text
        st.success("📘 Dictionary loaded")
    except Exception as e:
        st.error(f"❌ Failed to read dictionary: {e}")

# === CHAT HISTORY LOOP ===
for msg in st.session_state.chat.history:
    with st.chat_message(role_to_streamlit(msg.role)):
        st.markdown(msg.parts[0].text)

# === CHAT INPUT ===
if prompt := st.chat_input("💬 Ask Gemini something about your data..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add context
    df = st.session_state.dataframe
    if df is not None:
        sample = df.head(2).to_string()
        stats = df.describe(include="all").to_string()
        dict_text = st.session_state.dictionary or "No dictionary provided."
        df_name = "csv_data"

        full_prompt = f"""
You are a Python data assistant.
You will be given:
1. A pandas DataFrame called `{df_name}` already loaded in memory.
2. A sample and statistical summary of that dataset.
3. A data dictionary describing the columns.

**Data Preview:**
{sample}

**Statistical Summary:**
{stats}

**Data Dictionary:**
{dict_text}

User question:
{prompt}

👉 Generate only a Python code block that answers the question.
Do NOT explain the code.
Use `exec()` and save the final result in a variable called `ANSWER`.
"""

        try:
            # Send the prompt to Gemini
            csv_data = df.copy()
            response = st.session_state.chat.send_message(full_prompt)
            generated_code = response.text.replace("```python", "").replace("```", "").strip()

            with st.chat_message("assistant"):
                st.code(generated_code, language="python")  # Show code Gemini generated

            # Run the generated code safely
            local_vars = {"csv_data": csv_data}
            exec(textwrap.dedent(generated_code), {}, local_vars)

            # Display the final answer
            answer = local_vars.get("ANSWER", "No result found.")
            with st.chat_message("assistant"):
                if isinstance(answer, pd.DataFrame):
                    st.dataframe(answer)
                else:
                    st.markdown(f"**Result:** {answer}")

        except Exception as e:
            st.error(f"❌ Error executing Gemini code: {e}")

    else:
        st.warning("Please upload a CSV file to get started.")
