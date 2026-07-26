

import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


from ddgs import DDGS

from config import llm, embeddings



def create_vector_store(file_path, faiss_path):

    # Loading PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    print("PDF Loaded Successfully")

    # Splitting the document into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    print("Document Split Successfully")

    # Createing FAISS Vector Store
    vector_store = FAISS.from_documents(
        chunks,
        embeddings
    )

    print("Vector Store Created Successfully")

    vector_store.save_local(faiss_path)

    print("Vector Store Saved Successfully")
    print("PROJECT SUMMARY")
    print("Total Pages :", len(documents))
    print("Total Chunks:", len(chunks))

    return len(documents), len(chunks)


def search_web(question, max_results=5):
    context = ""

    with DDGS() as ddgs:

        try:
            results = ddgs.text(question, max_results=max_results)

            for result in results:

                title = result.get("title", "")
                body = result.get("body", "")
                href = result.get("href", "")

                context += f"Source: {title}\n{body}\nURL: {href}\n\n"

            print(f"\nWeb Search Retrieved {max_results} Results")

            return context

        except Exception as e:
            print(e)
            return "Web search is temporarily unavailable. Please try again."



def ask_question(question, mode, faiss_path):

    if mode == "document":

        print("\nSearching Uploaded Document...")

        if not os.path.exists(faiss_path):

            return "Please upload this document first."

        vector_store = FAISS.load_local(
            faiss_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

        retriever = vector_store.as_retriever(
            search_kwargs={"k": 3}
        )

        results = retriever.invoke(question)

        context = ""

        for doc in results:
            context += doc.page_content + "\n\n"

        prompt = f"""
            You are a helpful AI assistant.

            Answer ONLY using the provided context.

            If the answer is not present in the context,
            reply exactly:

            "I couldn't find that information in the uploaded document."

            Context:
            {context}

            Question:
            {question}

            Answer:
            """

        response = llm.invoke(prompt)


        print("QUESTION")

        print(question)

        print("\nRetrieved Chunks :", len(results))

        print("ANSWER")
    
        print(response.content)

        return response.content

  
    elif mode == "web":

        print("\nSearching the Web...")

        context = search_web(question)

    
        prompt = f"""
            You are a helpful AI assistant.

            Answer the question using the web search results below.

            If the results don't contain a clear answer,
            say so honestly instead of guessing.

            Web Search Results:
            {context}

            Question:
            {question}

            Answer:
            """

        response = llm.invoke(prompt)
        print("QUESTION")
        print(question)

  
        print("ANSWER")
        print(response.content)

        return response.content

 
    elif mode == "both":

        print("\nSearching Document + Web...")

        doc_context = ""

     
        if os.path.exists(faiss_path):

            vector_store = FAISS.load_local(
                faiss_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            retriever = vector_store.as_retriever(
                search_kwargs={"k": 3}
            )

            results = retriever.invoke(question)

            for doc in results:
                doc_context += doc.page_content + "\n\n"

        web_context = search_web(question)

        prompt = f"""
            You are a helpful AI assistant.

            Answer the question using BOTH the document context and the
            web search results below. Prefer the document if it directly
            answers the question, and use the web results to fill in
            anything the document doesn't cover.

            Document Context:
            {doc_context}

            Web Search Results:
            {web_context}

            Question:
            {question}

            Answer:
            """

        response = llm.invoke(prompt)
        print("QUESTION")
        print(question)
        print("ANSWER")
       
        print(response.content)

        return response.content

    
    else:

        return "Invalid search mode."