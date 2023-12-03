

import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
from llama_index.llms import Ollama
import requests
import json
import pickle

def authenticate(email, password):
    url = 'http://127.0.0.1:5000/authenticate'  # Replace with the actual URL of your Flask app

    # Replace with the actual data you want to send
    data = {
        'email': email,
        'password': password,
    }

    response = requests.post(url, data=data)
    response = json.loads(response.content.decode('utf-8'))
    return response["result"] == "success"



def login():
    st.title("Login Form")
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(email, password):
            st.success("Authentication successful!")
            st.session_state.is_authenticated = True
            st.session_state.email = email
            st.session_state.password = password
            st.session_state.runpage = default
            st.session_state.runpage()
            st.experimental_rerun()
        else:
            st.error("Authentication failed. Please try again.")


st.set_page_config(page_title="Local: Chat with your own content!", layout="wide", initial_sidebar_state="auto", menu_items=None)

st.image("logo.png", width=400)
st.title("Your content + your local AI language model = your privacy.")


@st.cache_resource(show_spinner=False)
def load_data(knowledgebase):
    with st.spinner(text="Loading and indexing docs – hang tight! This should take 1-2 minutes."):
        reader = SimpleDirectoryReader(input_dir=knowledgebase, recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(embed_model="local", llm=Ollama(model="zephyr", temperature=0.5))  #try model="zephyr" for better but slower results.
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

def get_models():
    url = 'http://127.0.0.1:5000/get_account_models'  # Replace with the actual URL of your Flask app

    # Replace with the actual data you want to send
    data = {
        'email': st.session_state.email,
        'password': st.session_state.password,
    }

    response = requests.post(url, data=data)
    models = json.loads(response.content.decode('utf-8'))["models"]
    return [model["model_name"] for model in models]

def get_model(model_name):
    st.session_state.service_context = ServiceContext.from_defaults(embed_model="local", llm=Ollama(model="zephyr", temperature=0.5))
    url = 'http://127.0.0.1:5000/get_model'  # Replace with the actual URL of your Flask app

    # Replace with the actual data you want to send
    data = {
        'email': st.session_state.email,
        'password': st.session_state.password,
        'model_name': model_name
    }

    response = requests.post(url, data=data)
    model = pickle.loads(response.content)
    chat = model.as_chat_engine(service_context=st.session_state.service_context, chat_mode="context", verbose=True)
    return chat


def handle_click(name):
    st.write(f"Button clicked for { name }")
    if name == "New Model":
        base()
    else:
        chat = get_model(name)
        st.session_state.chat_engine = chat
        if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

        if "messages" not in st.session_state.keys(): # Initialize the chat messages history
            st.session_state.messages = [
                {"role": "assistant", "content": "Ask me a question:"}
    ]

        for message in st.session_state.messages: # Display the prior chat messages
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = st.session_state.chat_engine.chat(prompt)
                    st.write(response.response)
                    lenght_sources = len(response.source_nodes)
                    with st.expander("Show References"):
                        for i in range(lenght_sources):
                            st.write(response.source_nodes[i].metadata)
                    
                    message = {"role": "assistant", "content": response.response}
                    st.session_state.messages.append(message) # Add response to message history


def base():
    knowledgebase = st.text_input("You are interacting with the content in this folder:", value="data" )
    system_prompt= st.text_area("Enter the role this AI assitant should play:" , value="You are my expert advisor. Assume that all questions are related to the data folder indicated above. For each fact you respond always include the reference document and page or paragraph. Keep your answers based on facts. Cite the source document next to each paragraph response you provide. Do not hallucinate features.")
    
    if "messages" not in st.session_state.keys(): # Initialize the chat messages history
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask me a question:"}
        ]
    index = load_data(knowledgebase)

    if "chat_engine" not in st.session_state.keys(): # Initialize the chat engine
            st.session_state.chat_engine = index.as_chat_engine(chat_mode="context", verbose=True) #modes might be "condense_question" or "context" or "simple"

    if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

    if "messages" not in st.session_state.keys(): # Initialize the chat messages history
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask me a question:"}
        ]

    for message in st.session_state.messages: # Display the prior chat messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_engine.chat(prompt)
                st.write(response.response)
                lenght_sources = len(response.source_nodes)
                with st.expander("Show References"):
                    for i in range(lenght_sources):
                        st.write(response.source_nodes[i].metadata)
                
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message) # Add response to message history

    if "messages" not in st.session_state.keys(): # Initialize the chat messages history
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask me a question:"}
        ]

def default():

    names = get_models() + ["New Model"]
    for name in names:
        # Create a button for each name
        button_clicked = st.button(name)

        # Check if the button is clicked
        if button_clicked:

            handle_click(name)

# Check if the user is authenticated
if not hasattr(st.session_state, 'is_authenticated') or not st.session_state.is_authenticated:
    login()
else:
    st.success("You are authenticated!")
    default()
    # Add your content for authenticated users here