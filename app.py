import streamlit as st
import pandas as pd
import google.generativeai as genai
 
# Page config
st.set_page_config(page_title="📊 CSV Chatbot with Gemini", layout="wide")
 
st.title("My Chatbot and Data Analysis App 😁")
st.write("Upload your dataset and ask questions in natural language!")
 
# API Key input
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
 
data_file = st.file_uploader("Upload Data Transation", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary", type=["csv", "txt"])
 
# Load files
if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded")
        st.write("### Preview of Data")
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
 
# Chat input
st.subheader("💬 Ask Questions About Your Data")
 
if prompt := st.chat_input("Ask me anything about your data..."):
    # Display user message
    st.session_state.chat_history.append(("user", prompt))
    st.chat_message("user").markdown(prompt)
 
    if model and st.session_state.dataframe is not None:
        try:
            # Build context for Gemini: data + dictionary
            df_desc = st.session_state.dataframe.describe(include='all').to_string()
            sample_data = st.session_state.dataframe.head(3).to_string()
            dict_info = st.session_state.dictionary or "No dictionary provided."
 
            
            system_prompt = f"""
            You are a helpful Python code generator.
            Your goal is to write Python code snippets based on the user's question
            and the provided DataFrame information.

            Here's the context:
            
            **User Question:**
            {question}
            
            **DataFrame Name:**
            {df_name}
            
            **DataFrame Details:**
            {data_dict_text}
            
            **Sample Data (Top 2 Rows):**
            {example_record}
            
            **Instructions:**
            1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
            2. **Crucially, use the `exec()` function to execute the generated code.**
            3. Do not import pandas.
            4. Change date column type to datetime.
            5. **Store the result of the executed code in a variable named `ANSWER`.**
               This variable should hold the answer to the user's question (e.g., a filtered DataFrame, a calculated value, etc.).
            6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`.
            7. Keep the generated code concise and focused on answering the question.
            8. If the question requires a specific output format (e.g., a list, a single value), ensure the `ANSWER` variable holds that format.
            
            **Example:**
            If the user asks: "Show me the rows where the 'age' column is greater than 30." 
            And the DataFrame has an 'age' column.
            
            The generated code should look like this (inside the `exec()` string):
            
            '''python
            query_result = {df_name}[{df_name}['age'] > 30]
            """
  
             response = model.generate_content(system_prompt + "\n\n" + prompt)
             answer = response.text
  
             st.session_state.chat_history.append(("assistant", answer))
             st.chat_message("assistant").markdown(answer)
  
         except Exception as e:
             st.error(f"⚠️ Error generating response: {e}")
    else:
        st.warning("⚠️ Please upload a CSV file and enter a valid API key.")
