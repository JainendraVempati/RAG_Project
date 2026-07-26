

from pymongo import MongoClient
from datetime import datetime




client = MongoClient("mongodb://localhost:27017")

db = client["RAG_Project"]

documents_collection = db["documents"]



def save_document(filename, filepath, faiss_path, pages, chunks):

    document = {

        "filename": filename,

        "filepath": filepath,

        "faiss_path": faiss_path,

        "pages": pages,

        "chunks": chunks,

        "uploaded_at": datetime.now()

    }

    documents_collection.insert_one(document)

    print("Document Saved in MongoDB")


def document_exists(filename):

    document = documents_collection.find_one({

        "filename": filename

    })

    return document is not None



def get_all_documents():

    documents = list(

        documents_collection.find(
            {},
            {
                "_id": 0,
                "filename": 1,
                "filepath": 1,
                "faiss_path": 1
            }
        )

    )

    return documents




def get_document(filename):

    document = documents_collection.find_one(

        {

            "filename": filename

        },

        {

            "_id": 0

        }

    )

    return document



def delete_document(filename):

    documents_collection.delete_one(

        {

            "filename": filename

        }

    )

    print("Document Deleted")