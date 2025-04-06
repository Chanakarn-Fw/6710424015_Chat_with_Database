import streamlit as st
import pandas as pd
import google.generativeai as genai
import textwrap

# === CONFIG ===
st.set_page_config(page_title="Gemini CSV Analyst", layout="wide")
st.title("CSV + Gemini: Ask Anything About Your Data")
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
    st.error(f"Error initializing Gemini: {e}")
    st.stop()

# === SESSION ===
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dictionary" not in st.session_state:
    st.session_state.dictionary = None

# === UPLOAD ===
st.subheader("Upload Your Dataset and Dictionary")
data_file = st.file_uploader("Upload CSV Data", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary (CSV or TXT)", type=["csv", "txt"])

if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("Data loaded")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")

if dict_file:
    try:
        if dict_file.name.endswith(".csv"):
            dict_df = pd.read_csv(dict_file)
            dict_text = dict_df.to_string(index=False)
        else:
            dict_text = dict_file.read().decode("utf-8")
        st.session_state.dictionary = dict_text
        st.success("Dictionary loaded")
    except Exception as e:
        st.error(f"Failed to read dictionary: {e}")

# === CHAT HISTORY LOOP ===
for msg in st.session_state.chat.history:
    with st.chat_message(role_to_streamlit(msg.role)):
        st.markdown(msg.parts[0].text)

# === CHAT INPUT ===
def safe_text(text):
    return text.encode('utf-8', 'ignore').decode('utf-8')

if prompt := st.chat_input("Ask Gemini something about your data..."):
    with st.chat_message("user"):
        st.markdown(safe_text(prompt))

    df = st.session_state.dataframe
    if df is not None:
        try:
            sample = df.head(2).to_string()
            stats = df.describe(include="all").to_string()
            dict_text = st.session_state.dictionary or "No dictionary provided."
            df_name = "csv_data"

            # 1. Prompt Gemini to generate Python code
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

Generate only a Python code block that answers the question.
Do NOT explain the code.
Use `exec()` and save the final result in a variable called `ANSWER`.
"""

            csv_data = df.copy()
            response = model.generate_content(full_prompt)
            generated_code = response.text.replace("```python", "").replace("```", "").strip()

            # 2. Execute code
            local_vars = {"csv_data": csv_data}
            exec(textwrap.dedent(generated_code), {}, local_vars)
            answer = local_vars.get("ANSWER", "No result found.")

            # 3. Display answer
            with st.chat_message("assistant"):
                if isinstance(answer, pd.DataFrame):
                    st.dataframe(answer)
                else:
                    st.markdown(f"**Result:** {safe_text(str(answer))}")

            # 4. Ask Gemini to summarize the result naturally
            explain_prompt = f"""
The user asked: {prompt}
Here is the result: {answer}

Now, explain the answer clearly.
Summarize the result and include your opinion on the customer's persona based on the data.
"""
            explanation = model.generate_content(explain_prompt)
            with st.chat_message("assistant"):
                st.markdown(safe_text(explanation.text))

            # 5. Save clean chat history (only prompt and summary, not code)
            st.session_state.chat.history.append({"role": "user", "parts": [{"text": safe_text(prompt)}]})
            st.session_state.chat.history.append({"role": "model", "parts": [{"text": safe_text(str(answer))}]})

        except Exception as e:
            st.error(f"Error executing or interpreting Gemini code: {e}")

    else:
        st.warning("Please upload a CSV file to get started.")
