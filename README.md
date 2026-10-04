# 📚 Document-Aware RAG System

A **Retrieval-Augmented Generation (RAG)** application that allows users to upload PDF documents and ask questions about them using an AI model.

The system can answer questions using:

- 📄 **Uploaded Document** — searches only the selected PDF.
- 🌐 **Web Search** — searches the web for relevant information.
- 🔄 **Document + Web** — searches both the uploaded document and the web, combining the retrieved information.

The project uses **LangChain, FAISS, MongoDB, FastAPI, PyPDF, DuckDuckGo Search, and an LLM** to build the complete RAG pipeline.

---

## 🚀 Key Feature

The main feature of this project is **conditional information retrieval**.

When a user asks a question, the system can determine where the information should come from based on the selected search mode.

### Retrieval Modes

| Mode | Information Source | Description |
|---|---|---|
| `document` | 📄 PDF | Searches only the uploaded document |
| `web` | 🌐 Web | Searches the internet using DuckDuckGo |
| `both` | 📄 + 🌐 | Searches both the uploaded document and web |

For example:

```text
User Question:
"What is the architecture discussed in this document?"

Mode:
document

        ↓

FAISS Vector Search

        ↓

Relevant PDF Chunks

        ↓

LLM

        ↓

Answer
```

If the required information is not available in the document, the `document` mode does **not** make a web search. Instead, it tells the user that the information could not be found.

With `both` mode, the document is searched first and web results are also retrieved. The LLM is instructed to prefer the document when it directly answers the question and use web results to supplement missing information.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI Server   │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              Upload PDF       Ask Question     Documents
                    │               │
                    ▼               │
              PyPDFLoader           │
                    │               │
                    ▼               │
          Recursive Text Splitter   │
                    │               │
                    ▼               │
             Embeddings             │
                    │               │
                    ▼               │
                 FAISS              │
                    │               │
                    └───────┐       │
                            │       │
                            ▼       ▼
                         Retrieval
                            │
                  ┌─────────┼─────────┐
                  │         │         │
                  ▼         ▼         ▼
              Document     Web       Both
              Search      Search     Search
                  │         │         │
                  └─────────┼─────────┘
                            │
                            ▼
                           LLM
                            │
                            ▼
                         Answer
```

---

# 🧠 How RAG Works in This Project

RAG stands for:

> **Retrieval-Augmented Generation**

Instead of asking the LLM to answer a question only from its internal knowledge, this project first retrieves relevant information and then provides that information to the LLM as context.

The process is:

```text
PDF
 ↓
Load Document
 ↓
Split into Chunks
 ↓
Generate Embeddings
 ↓
Store Embeddings in FAISS
 ↓
User Asks Question
 ↓
Similarity Search
 ↓
Retrieve Relevant Chunks
 ↓
Send Context + Question to LLM
 ↓
Generate Answer
```

This helps the model answer questions based on the uploaded document rather than relying only on its pretrained knowledge.

---

# 📄 1. Document Upload Pipeline

When a user uploads a PDF, the application performs several steps.

## Step 1 — Upload PDF

The FastAPI `/upload` endpoint receives the uploaded PDF.

```python
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
```

The file is stored inside:

```text
uploads/
```

Example:

```text
uploads/
└── research_paper.pdf
```

---

## Step 2 — Check Duplicate Documents

Before processing the document, MongoDB is checked.

```python
if document_exists(file.filename):
```

If the document already exists, the application does not create another FAISS index.

It returns:

```text
Document already exists. Using the existing index.
```

This avoids unnecessary processing.

---

# 📖 2. PDF Loading

The project uses `PyPDFLoader` from LangChain.

```python
loader = PyPDFLoader(file_path)
documents = loader.load()
```

The PDF is converted into LangChain `Document` objects.

Each document contains information such as:

- Page content
- Page metadata
- Source information

---

# ✂️ 3. Text Chunking

Large documents are divided into smaller pieces using:

```python
RecursiveCharacterTextSplitter
```

Configuration:

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
```

### Chunk Size

Each chunk can contain approximately 1000 characters.

### Chunk Overlap

Adjacent chunks overlap by approximately 200 characters.

For example:

```text
Chunk 1
-------------------------
A B C D E F G H I J
             ↑
             overlap
             ↓
Chunk 2
             G H I J K L M N
```

The overlap helps prevent important information from being lost when a sentence or concept is split between chunks.

---

# 🔢 4. Embeddings

After splitting the document into chunks, the project converts the chunks into numerical vector representations using the configured embedding model.

```python
vector_store = FAISS.from_documents(
    chunks,
    embeddings
)
```

Embeddings represent the semantic meaning of the text as vectors.

For example:

```text
"Machine learning is a subset of AI"
```

is converted into a numerical vector.

Similar concepts produce vectors that are closer together in vector space.

---

# 🗂️ 5. FAISS Vector Database

The project uses **FAISS** for vector similarity search.

FAISS stores the embeddings generated from the document.

The index is saved locally:

```python
vector_store.save_local(faiss_path)
```

The project creates:

```text
faiss_index/
```

Example:

```text
faiss_index/
└── research_paper/
    ├── index.faiss
    └── index.pkl
```

When a user asks a question, FAISS searches for the most semantically relevant chunks.

---

# 🗄️ 6. MongoDB

MongoDB is used to store **document metadata**.

Database:

```text
RAG_Project
```

Collection:

```text
documents
```

Each document contains information such as:

```json
{
    "filename": "research_paper.pdf",
    "filepath": "uploads/research_paper.pdf",
    "faiss_path": "faiss_index/research_paper",
    "pages": 10,
    "chunks": 35,
    "uploaded_at": "..."
}
```

### MongoDB stores:

- Filename
- File path
- FAISS index path
- Number of pages
- Number of chunks
- Upload time

### FAISS stores:

- Document embeddings
- Vector index
- Chunk information required for retrieval

Therefore, MongoDB and FAISS have different responsibilities.

```text
MongoDB
   │
   └── Document Metadata

FAISS
   │
   └── Document Vector Index
```

---

# 🔍 7. Question Answering

The `/ask` endpoint receives the question.

```python
@app.post("/ask")
async def ask(data: Question):
```

The request contains information such as:

```text
filename
question
mode
```

The system first checks whether the selected document exists in MongoDB.

If it does not exist:

```text
Document not found.
```

The API also returns:

```json
{
    "allow_web_search": true
}
```

This allows the frontend to offer web search when the selected document is unavailable.

---

# 📄 Document Search Mode

When:

```text
mode = document
```

the system searches only the uploaded document.

First, the FAISS index is loaded:

```python
vector_store = FAISS.load_local(
    faiss_path,
    embeddings,
    allow_dangerous_deserialization=True
)
```

A retriever is created:

```python
retriever = vector_store.as_retriever(
    search_kwargs={"k": 3}
)
```

This retrieves the **top 3 relevant chunks**.

```python
results = retriever.invoke(question)
```

The retrieved chunks are combined into a context.

The LLM then receives:

```text
Context + Question
```

The prompt instructs the model:

```text
Answer ONLY using the provided context.
```

If the information is not found, the model is instructed to return:

```text
I couldn't find that information in the uploaded document.
```

### Important

In `document` mode, the system **does not automatically search the web** when the answer is missing.

This keeps the answer strictly document-based.

---

# 🌐 Web Search Mode

When:

```text
mode = web
```

the application does not use FAISS.

Instead, it calls:

```python
search_web(question)
```

The project uses **DuckDuckGo Search** through:

```python
from ddgs import DDGS
```

The system retrieves up to 5 search results by default.

Each result contains:

```text
Title
Body
URL
```

These results are combined into a context.

The LLM then receives:

```text
Web Search Results
+
Question
```

and generates the answer.

---

# 🔄 Document + Web Mode

When:

```text
mode = both
```

the application searches both sources.

```text
                 User Question
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
          FAISS Search      Web Search
              │                 │
              ▼                 ▼
       Document Context    Web Context
              │                 │
              └────────┬────────┘
                       │
                       ▼
                      LLM
                       │
                       ▼
                    Answer
```

The document context and web context are sent together to the LLM.

The prompt instructs the LLM:

> Prefer the document if it directly answers the question, and use web results to fill in anything the document doesn't cover.

This makes the `both` mode useful when:

- The document contains some information but not everything.
- Current information is needed.
- Additional context is required.
- The user wants information from both the uploaded material and the web.

---

# 🧩 Retrieval Decision Logic

The project currently supports three explicit retrieval conditions.

```text
                  User Question
                       │
                       ▼
                Selected Mode
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
      document        web          both
          │            │            │
          ▼            ▼            ▼
        FAISS       DuckDuckGo   FAISS + Web
          │            │            │
          └────────────┼────────────┘
                       ▼
                       LLM
                       │
                       ▼
                     Answer
```

### Document

```text
PDF → FAISS → Relevant Chunks → LLM
```

### Web

```text
Question → DuckDuckGo → Search Results → LLM
```

### Both

```text
PDF → FAISS ─────────┐
                     ├──→ LLM → Answer
Question → Web ─────┘
```

---

# 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| FastAPI | Backend REST API |
| LangChain | RAG pipeline and document processing |
| PyPDFLoader | PDF loading |
| RecursiveCharacterTextSplitter | Text chunking |
| FAISS | Vector similarity search |
| Embeddings | Convert text into vectors |
| MongoDB | Store document metadata |
| PyMongo | MongoDB connection |
| DDGS | Web search |
| LLM | Generate final answers |
| Jinja2 | HTML template rendering |
| HTML/CSS/JavaScript | Frontend |

---

RAG_Project/
│
├── faiss_index/          # Stores FAISS vector indexes
│
├── static/               # Frontend static files
│   ├── CSS files
│   └── JavaScript files
│
├── templates/            # HTML templates
│   └── index.html
│
├── uploads/              # Uploaded PDF documents
│
├── .gitignore            # Git ignored files
├── README.md             # Project documentation
├── app.py                # FastAPI application and API endpoints
├── config.py             # LLM and embedding configuration
├── database.py           # MongoDB database operations
├── rag.py                # RAG, FAISS and web-search logic
├── requirements.txt      # Python dependencies
├── schemas.py            # Pydantic request schemas
└── theory.txt            # RAG/project theoretical notes

# ⚙️ Configuration

The project uses:

```python
from config import llm, embeddings
```

Therefore, the LLM and embedding configuration should be defined in:

```text
config.py
```

Example structure:

```python
# config.py

# Configure your LLM
# Configure your embedding model
```

API keys should be stored using environment variables rather than directly writing them in the source code.

Example:

```env
LLM_API_KEY=your_api_key
```

---

# 🗄️ MongoDB Setup

The project currently connects to MongoDB using:

```python
client = MongoClient("mongodb://localhost:27017")
```

The database is:

```text
RAG_Project
```

and the collection is:

```text
documents
```

Make sure MongoDB is running before starting the application.

---

# 📦 Installation

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd RAG_Project
```

---

## 2. Create Virtual Environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you do not have a `requirements.txt`, the major packages used by the project include:

```text
fastapi
uvicorn
langchain
langchain-community
langchain-text-splitters
faiss-cpu
pypdf
pymongo
ddgs
python-multipart
jinja2
```

You also need the package required by the particular LLM and embedding model configured in `config.py`.

---

# ▶️ Running the Application

Start the FastAPI server using:

```bash
uvicorn main:app --reload
```

The application will normally be available at:

```text
http://127.0.0.1:8000
```

The FastAPI API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# 🔌 API Endpoints

## `GET /`

Loads the main frontend page.

```text
GET /
```

---

## `POST /upload`

Uploads and indexes a PDF document.

```text
POST /upload
```

### Process

```text
Upload PDF
    ↓
Check MongoDB
    ↓
Save PDF
    ↓
Load PDF
    ↓
Split into Chunks
    ↓
Generate Embeddings
    ↓
Create FAISS Index
    ↓
Save FAISS Index
    ↓
Save Metadata in MongoDB
```

Example response:

```json
{
    "message": "Document uploaded and indexed successfully.",
    "filename": "research_paper.pdf",
    "total_pages": 10,
    "total_chunks": 35
}
```

---

# `POST /ask`

Used to ask a question.

```text
POST /ask
```

The request contains:

```json
{
    "filename": "research_paper.pdf",
    "question": "What is the proposed methodology?",
    "mode": "document"
}
```

Possible modes:

```text
document
web
both
```

---

# `GET /documents`

Returns all uploaded documents stored in MongoDB.

```text
GET /documents
```

Example:

```json
[
    {
        "filename": "research_paper.pdf",
        "filepath": "uploads/research_paper.pdf",
        "faiss_path": "faiss_index/research_paper"
    }
]
```

---

# `GET /document/{filename}`

Returns information about a specific uploaded document.

Example:

```text
GET /document/research_paper.pdf
```

---

# 🧠 Example Workflow

Suppose the user uploads:

```text
Machine_Learning.pdf
```

The application processes it:

```text
Machine_Learning.pdf
        ↓
PyPDFLoader
        ↓
Text Extraction
        ↓
Chunking
        ↓
Embeddings
        ↓
FAISS
```

MongoDB stores:

```text
Machine_Learning.pdf
        │
        ├── File Path
        ├── FAISS Path
        ├── Number of Pages
        ├── Number of Chunks
        └── Upload Time
```

Now the user asks:

```text
"What is transfer learning?"
```

### If mode = document

```text
Question
   ↓
FAISS
   ↓
Top 3 Relevant Chunks
   ↓
LLM
   ↓
Answer
```

### If mode = web

```text
Question
   ↓
DuckDuckGo
   ↓
Web Results
   ↓
LLM
   ↓
Answer
```

### If mode = both

```text
                Question
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
        FAISS              Web Search
          │                   │
          ▼                   ▼
     PDF Context          Web Context
          │                   │
          └─────────┬─────────┘
                    ▼
                   LLM
                    ↓
                  Answer
```

---

# 🎯 Why Use FAISS?

A normal keyword search looks for exact words.

For example:

```text
Question:
"What is the process of teaching machines?"
```

The document might say:

```text
"Machine learning enables systems to learn from data."
```

Even though the exact words may be different, embedding-based retrieval can identify that these concepts are semantically related.

FAISS performs efficient similarity search over these vector representations.

---

# 🎯 Why Use RAG?

A general LLM may not know the contents of a user's private PDF.

For example:

```text
User's Research Paper
        ↓
       RAG
        ↓
Relevant information retrieved
        ↓
       LLM
        ↓
Answer based on the research paper
```

This allows the application to work with user-provided documents.

---

# 🔐 Document-Grounded Answers

The document mode uses a strict prompt:

```text
Answer ONLY using the provided context.
```

If the retrieved context does not contain the answer, the system instructs the model to respond:

```text
I couldn't find that information in the uploaded document.
```

This reduces the chance of the model inventing information that is not present in the uploaded document.

---

# 🌐 Why Add Web Search?

Documents can become outdated or may not contain all required information.

For example, a PDF might explain:

```text
"What is Kubernetes?"
```

But the user may ask:

```text
"What is the latest Kubernetes version?"
```

The uploaded document may not contain current information.

Web search can provide additional and more recent information.

Therefore, the project provides:

```text
Document Search
+
Web Search
```

instead of depending entirely on one source.

---

# 🔄 Advantages of the `Both` Mode

The combined mode provides two sources of information.

### Document

Useful for:

- Private information
- Research papers
- Notes
- Company documents
- Course material
- Project documentation

### Web

Useful for:

- Current information
- Missing information
- Additional context
- Information not present in the PDF

The LLM combines both sources to produce the final response.

---

# 📊 RAG Pipeline Summary

```text
                 PDF Upload
                     │
                     ▼
               PyPDFLoader
                     │
                     ▼
              Text Extraction
                     │
                     ▼
             Text Chunking
                     │
                     ▼
               Embeddings
                     │
                     ▼
                  FAISS
                     │
                     ▼
             Store Vector Index
                     │
                     │
              User Question
                     │
                     ▼
               Search Mode
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
       Document     Web        Both
          │          │          │
          ▼          ▼          ▼
        FAISS      DDGS      FAISS + DDGS
          │          │          │
          └──────────┼──────────┘
                     ▼
                    LLM
                     │
                     ▼
              Generated Answer
```

---

# 🧪 Example Questions

After uploading a research paper, users can ask:

```text
What is the main objective of this paper?
```

```text
What methodology is proposed?
```

```text
What dataset was used?
```

```text
What models were used?
```

```text
What are the limitations of the proposed approach?
```

For current information, users can switch to:

```text
Web
```

For information requiring both the research paper and current web information:

```text
Both
```

---

# ⚠️ Important Design Considerations

### 1. FAISS is local

The FAISS index is stored on the server's filesystem.

```text
faiss_index/
```

If the application is deployed to a hosting platform with temporary storage, the FAISS indexes may not persist after a restart or redeployment unless persistent storage is configured.

---

### 2. MongoDB and FAISS are separate

MongoDB does not contain the actual vector embeddings in this implementation.

MongoDB stores metadata and the location of the FAISS index.

```text
MongoDB
    ↓
"Where is this document's FAISS index?"

FAISS
    ↓
"Which chunks are relevant to this question?"
```

---

### 3. `both` mode does not mean automatic fallback

The current implementation of `both` explicitly searches both sources.

The logic is:

```text
Document Search + Web Search
```

It is not:

```text
Document Search
     ↓
If answer missing
     ↓
Web Search
```

That distinction is important.

---

# 🚧 Current Limitations

- Currently focused on PDF documents.
- FAISS indexes are stored locally.
- Web search depends on the availability of DuckDuckGo search.
- The quality of answers depends on the embedding model, retrieved chunks, web results, and LLM.
- Only the top 3 document chunks are retrieved in the current configuration.
- Web search retrieves up to 5 results by default.
- MongoDB must be available for document metadata.
- The system does not currently maintain conversation memory between questions.
- The system does not automatically cite individual document chunks in the generated answer.

---

# 🔮 Future Improvements

Possible improvements include:

### 1. Automatic Retrieval Routing

Instead of manually selecting:

```text
document
web
both
```

the system could classify the question automatically.

```text
                    Question
                       │
                       ▼
                Query Classifier
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     Document         Web            Both
```

---

### 2. Source Citations

The application could show:

```text
Answer

Sources:
📄 Page 4
📄 Page 7
🌐 Source 1
🌐 Source 2
```

This would make the RAG system more transparent.

---

### 3. Conversation Memory

The system could remember previous questions.

Example:

```text
User:
What model did the paper use?

AI:
XGBoost.

User:
Why did they choose it?
```

The second question could use the previous conversation to understand what "it" refers to.

---

### 4. Reranking

A reranker could be added after FAISS retrieval:

```text
FAISS
 ↓
Retrieve 10–20 chunks
 ↓
Reranker
 ↓
Best 3 chunks
 ↓
LLM
```

This can improve retrieval quality.

---

### 5. More Document Formats

Future versions could support:

```text
PDF
DOCX
TXT
CSV
Web Pages
Markdown
```

---

# 🔒 Security Notes

Do not commit API keys to GitHub.

Avoid:

```python
API_KEY = "actual-secret-key"
```

Use environment variables instead.

Also, the current code uses:

```python
allow_dangerous_deserialization=True
```

when loading FAISS.

Only load FAISS indexes that are trusted and generated by your application.

---

# 📌 Project Summary

This project is a **Document-Aware Retrieval-Augmented Generation system**.

It combines private document retrieval with web search.

The main pipeline is:

```text
PDF
 ↓
PyPDFLoader
 ↓
Chunking
 ↓
Embeddings
 ↓
FAISS
 ↓
Semantic Retrieval
 ↓
LLM
 ↓
Answer
```

For web-based questions:

```text
Question
 ↓
DuckDuckGo Search
 ↓
Search Results
 ↓
LLM
 ↓
Answer
```

For combined questions:

```text
PDF → FAISS ───────┐
                   ├──→ LLM → Final Answer
Web → DuckDuckGo ──┘
```

The application uses **FastAPI as the backend, MongoDB for document metadata, FAISS for vector retrieval, LangChain for the RAG pipeline, DuckDuckGo for web search, and an LLM for final answer generation.**

---

# 👨‍💻 Author

**Jainendra**

RAG / Generative AI Project

---
