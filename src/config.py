import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
api_key=os.getenv("GROQ_API")


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, api_key=api_key)
llm_for_pg = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, api_key=api_key)