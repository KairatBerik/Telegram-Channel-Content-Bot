import llama_cpp
from llama_cpp import Llama 
from langchain_community.llms.llamacpp import LlamaCpp
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import CTransformers
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import streamlit as st 
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re 

st.set_page_config(layout='wide')

st.sidebar.title("Pick your Telegram Channel")
st.sidebar.divider()
st.title("Telegram Channel Content Bot")
st.divider()
st.header("Chat with the Bot")


input_link = st.sidebar.text_input(label="", placeholder='upload your link from TGSTAT.com')

path = ''

service = Service(Executable_path = path)
driver = webdriver.Chrome(service = service)

if input_link:
    driver.get(input_link)
    
    
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.post-container'))
    )

  
    products = driver.find_elements(By.CSS_SELECTOR, 'div.post-container')

    txt = []
    dates = []

    for x in products:
        txt.append(x.find_element(By.CSS_SELECTOR, 'div.post-text').text)
        dates.append(x.find_element(By.CSS_SELECTOR, 'p.text-muted').text)

    num_clicks = int(st.sidebar.radio(
        "How many posts? (in 20s)",
        ["1", "2", "3"]))

    for _ in range(num_clicks):
        try:
            buttons = driver.find_element(By.CSS_SELECTOR, 'div.lm-button-container.mt-2.height-36px')
            buttons.click()
            time.sleep(5)
            new_products = driver.find_elements(By.CSS_SELECTOR, 'div.post-container')

            for x in new_products[len(products):]:
                txt.append(x.find_element(By.CSS_SELECTOR, 'div.post-text').text)
                dates.append(x.find_element(By.CSS_SELECTOR, 'p.text-muted').text)

            products = new_products

        except Exception as e:
            st.sidebar.write(f"Error occurred: {e}")
            break

 
    df = pd.DataFrame({"txt": txt, "date": dates})
    df.to_csv("tg.csv", index=True)
    driver.quit()
    st.sidebar.write("Link Uploaded Successfully")
else:
    st.sidebar.write("No Link yet")
    
def chat_with_csv(prompt):
        chat_history=[]
        if prompt:
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = qa({"question":prompt, "chat_history": chat_history})
            with st.chat_message("assistant"):
                st.markdown(re.sub(r'<.|assistant.|>',"",response['answer']))
            st.session_state.messages.append({"role": "assistant", "content": re.sub(r'<.|assistant.|>',"",response['answer'])})
        if prompt == 'exit':
            print('Exiting')
            sys.exit()


if input_link:
    loader = CSVLoader(file_path="tg.csv", encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
    chunks = text_splitter.split_documents(data)

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local('vectorstore/dbfaiss')

    llm = LlamaCpp(model_path='', temperature=0.1, max_tokens=2000)
    qa = ConversationalRetrievalChain.from_llm(llm=llm, retriever=db.as_retriever())
   
    if "messages" not in st.session_state:
        st.session_state.messages = []


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Enter your question about the content of this channel")
    chat_with_csv(prompt)
    
