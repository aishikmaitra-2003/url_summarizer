import streamlit as st
import validators
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader,UnstructuredURLLoader

load_dotenv()
#Streamlit Configurer
st.set_page_config(page_title="LangChain Summarizer for Urls:",page_icon="❤️")
st.title("Langchain Url Summarizer")
st.subheader("Project here")

#Groq API Key
groq_api_key = os.getenv("GROQ_KEY")
llm=ChatGroq(model="llama-3.1-8b-instant",groq_api_key=groq_api_key)
# prompt_template="""
# Provide a summary of the following content in 500 words:
# content:{text}
# ....
# """
# prompt=prompt_template(template=prompt_template,input_variables=["text"])

from langchain.prompts import PromptTemplate

prompt_template = """
Provide a summary of the following content in 500 words:
content: {text}
"""

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["text"]
)
generic_url=st.text_input("Enter the test url here:",label_visibility="collapsed")
if st.button("Summarize"):
    if not groq_api_key.strip() or not generic_url.strip():
        st.error("Please Enter the URL")
    elif not validators.url(generic_url):
        st.error("Please enter a valid url")
    else:
        try:
            with st.spinner("Loading...."):
                if "youtube.com" in generic_url:
                    loader=YoutubeLoader.from_youtube_url(generic_url,add_video_info=True)
                else:
                    loader=UnstructuredURLLoader(urls=[generic_url],ssl_verify=False,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
                data=loader.load()
                chain=load_summarize_chain(llm,chain_type="stuff",prompt=prompt)
                output=chain.run(data)
                st.success(output)
        except Exception as e:
            st.exception(f"The exception is {e}")
