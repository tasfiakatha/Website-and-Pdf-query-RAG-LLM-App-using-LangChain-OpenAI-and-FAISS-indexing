"""
This script demonstrate how to deploy and serve RAG based chatbot using Streamlit.

In this setup, we’ll deploy a local server that will host a Streamlit-based GUI
(Graphical User Interface). This GUI will allow users to interact directly with
the Language Model (LLM) through an intuitive, user-friendly interface.

The local system will work as a server that provides real-time responses to the
user's inputs in the GUI.

Requirements
------------
Install requirements.txt from command prompt: pip install -r requirements.txt

To run the app on local host:
---------------
Run in command prompt:
streamlit run main.py

"""



import nltk
import os
import tempfile
import pickle
import streamlit as st
import time
import openai
import langchain 
from langchain.llms import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.qa_with_sources.loading import load_qa_with_sources_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader, UnstructuredFileLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from secret_key import openapi_key
os.environ['OPENAI_API_KEY'] = openapi_key 


# Get all environment variables
from dotenv import load_dotenv
load_dotenv()


# Web interface
st.title("DataScout AI")
st.sidebar.subheader("Websites")

urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i+1}")
    urls.append(url)

# File upload 
st.sidebar.subheader('Upload documents')
uploaded_files = st.sidebar.file_uploader("Select files from your computer", type=['txt','pdf','docx'], accept_multiple_files=True)

process_url_clicked = st.sidebar.button("Get content")

# progress bar
main_placefolder = st.empty()

# Filepath location
file_path = "faiss_index\index.pkl"

# Initialize llm 
llm = OpenAI(temperature=0.6, max_tokens=500)

if process_url_clicked:
    # load data from URLs
    data = []
    if any(urls):
        loader = UnstructuredURLLoader(urls=urls)
        main_placefolder.text("Loading your data. . . . ⏳")
        data.extend(loader.load())
    
    # load data from uploaded documents
    if uploaded_files:
        for file in uploaded_files:

            # create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_file_path = tmp_file.name
            
            # temporary file path for UnstructuredFileLoader
            file_loader = UnstructuredFileLoader(tmp_file_path)
            main_placefolder.text(f"Loading file: {file.name}. . . . 📂")
            data.extend(file_loader.load())

            # delete temporary file after processing
            os.remove(tmp_file_path)

    # split data
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000
    )
    main_placefolder.text("Splitting your data. . . . ✂")
    docs = text_splitter.split_documents(data)

    # embeddings
    # Store in FAISS index
    embeddings = OpenAIEmbeddings()
    vectorstore_openai = FAISS.from_documents(docs, embeddings)
    main_placefolder.text("Creating embedding vector. . . . 📚")
    time.sleep(2)

    # Directory to save FAISS index
    faiss_index_dir = "faiss_index"
    if not os.path.exists(faiss_index_dir):
        os.makedirs(faiss_index_dir)

    # Save faiss index on local computer
    vectorstore_openai.save_local(faiss_index_dir)
    print("FAISS index saved successfully")

# Question box and submit button
with st.form("query_form"):
    query = st.text_input("What do you want to know?", "")
    enter_button = st.form_submit_button("Enter")

if enter_button:
    if query:
        # Load FAISS index from directory
        if os.path.exists("faiss_index"):
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            print("FAISS index loaded successfully")

            # Create retrieval QA chain
            chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=vectorstore.as_retriever())
            result = chain({"question":query}, return_only_outputs=True)

            # {"answer":" ", "sources":" "}
            st.header("Answer")
            st.write(result["answer"])

            # Display sources
            sources = result.get("sources", "")
            if sources:
                st.subheader("Sources:")
                sources_list = sources.split("\n")
                for source in sources_list:
                    st.write(source)



