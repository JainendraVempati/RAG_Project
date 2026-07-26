
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings



load_dotenv()



llm = ChatGoogleGenerativeAI(

    model="gemini-2.5-flash",

    temperature=0

)



embeddings = HuggingFaceEmbeddings(

    model_name="BAAI/bge-small-en-v1.5"

)