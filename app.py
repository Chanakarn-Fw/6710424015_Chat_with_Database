import streamlit as st
import pandas as pd
import google.generativeai as genai
import textwrap

# Page config
st.set_page_config(page_title="📊 CSV Chatbot with Gemini", layout="wide")

st.title("📊 Chat with Your CSV using Gemini 😁")
st.write("Upload your dataset and ask questions in natural language!")

# Load API key
gemini_api_key = st.secrets['gemini_api_key']
model = None

if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("✅ Gemini API Key configured.")
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {e}")

# Session state init
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

if "dictionary" not in st.session_state:
    st.session_state.dictionary = None

# File upload
st.subheader("📤 Upload CSV and Optional Dictionary")

data_file = st.file_uploader("Upload Data CSV", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary (CSV or TXT)", type=["csv", "txt"])

# Load files
if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error reading data file: {e}")

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
        st.error(f"❌ Error reading dictionary file: {e}")

# Ask questions
st.subheader("💬 Ask About Your Data")

if prompt := st.chat_input("Ask me anything about your data..."):
    st.session_state.chat_history.append(("user", prompt))
    st.chat_message("user").markdown(prompt)

    if model and st.session_state.dataframe is not None:
        try:
            df_name = "csv_data"
            st.session_state.dataframe.columns = st.session_state.dataframe.columns.str.strip()
            csv_data = st.session_state.dataframe
            csv_description = csv_data.describe(include='all').fillna("").to_string()
            sample_data = csv_data.head(3).to_string()
            dictionary = st.session_state.dictionary or "No dictionary provided."

            # Prompt to Gemini
            full_prompt = f"""
You are a helpful Python code generator.

User uploaded a DataFrame called `{df_name}`.

**Data Dictionary (if any):**
{dictionary}

**Data Description:**
{csv_description}

**Sample Rows:**
{sample_data}

Now, answer this question from the user:  
"{prompt}"

Write Python code to solve it.  
- Store the result in a variable named ANSWER.  
- Do not import pandas.  
- Assume `{df_name}` is already loaded.
"""

            response = model.generate_content(full_prompt)
            code = response.text.replace("```python", "").replace("```", "")
            query = textwrap.dedent(code)

            local_vars = {df_name: csv_data}

            # Execute the generated code
            exec(query, {}, local_vars)

            # Retrieve the result
            answer = local_vars.get("ANSWER", "No ANSWER returned.")

            # Display result
            st.chat_message("assistant").markdown(f"**Answer:**\n{answer}")
            st.session_state.chat_history.append(("assistant", str(answer)))

        except Exception as e:
            st.error(f"⚠️ Error during code execution: {e}")

    else:
        st.warning("⚠️ Please upload a CSV file and ensure the API key is valid.")


